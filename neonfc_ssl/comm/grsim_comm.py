import logging
import socket
from neonfc_ssl.protocols.grSim.grSim_Commands_pb2 import grSim_Commands
from neonfc_ssl.protocols.grSim.grSim_Packet_pb2 import grSim_Packet
from neonfc_ssl.control import Control


class GrComm:
    def __init__(self, game):
        self._game = game
        self._config = self._game.config

        # Control Layer Class
        self._control: Control = None

        # GrSim Comm Classes
        self.commands = []
        self.command_sock = None

        # GrSim Comm Parameters
        self.command_port = self._config['network']['command_port']
        self.host = self._config['network']['host_ip']

        # Coach Layer Logger
        self.logger = logging.getLogger("comm")

    def start(self):
        self.logger.info("Starting GRSim communication...")

        self._control = self._game.control

        self.logger.info(f"Creating socket with address: {self.host} and port: {self.command_port}")
        self.command_sock = self._create_socket()

        self.logger.info("GRSim communication module started!")

    def freeze(self):
        commands = grSim_Commands()
        commands.isteamyellow = self._config['match']['team_color'] == 'yellow'
        commands.timestamp = 0

        for robot in self._config['match']['robots_ids']:
            command = commands.robot_commands.add()
            command.wheel1 = 0
            command.wheel2 = 0
            command.wheel3 = 0
            command.wheel4 = 0

            command.kickspeedx = 0
            command.kickspeedz = 0
            command.veltangent = 0
            command.velnormal = 0
            command.velangular = 0

            command.spinner = False
            command.wheelsspeed = True
            command.id = robot

        self.send(commands)
    
    def update(self):
        cmds = self._control.commands
        self._control.new_data = False

        commands = grSim_Commands()
        commands.isteamyellow = self._config['match']['team_color'] == 'yellow'
        commands.timestamp = 0

        for robot in cmds:
            robot.global_speed_to_wheel_speed()
            command = commands.robot_commands.add()
            command.wheel1 = robot.wheel_speed[0]
            command.wheel2 = robot.wheel_speed[1]
            command.wheel3 = robot.wheel_speed[2]
            command.wheel4 = robot.wheel_speed[3]
            command.kickspeedx = robot.kick_speed[0]
            command.kickspeedz = robot.kick_speed[1]
            command.veltangent = 0
            command.velnormal = 0
            command.velangular = 0
            command.spinner = robot.spinner
            command.wheelsspeed = True
            command.id = robot.robot.robot_id

        self.send(commands)

    def send(self, commands):
        packet = grSim_Packet()
        packet.commands.CopyFrom(commands)

        self.command_sock.sendto(
            packet.SerializeToString(),
            (self.host, self.command_port)
        )

    def _create_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
