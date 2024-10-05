import logging
import socket

from neonfc_ssl.protocols.grSim.grSim_Commands_pb2 import grSim_Commands
from neonfc_ssl.protocols.grSim.grSim_Packet_pb2 import grSim_Packet


class GrComm(object):
    def __init__(self, game):
        super(GrComm, self).__init__()

        self.commands = []
        self._game = game
        self.config = self._game.config
        self._coach = None

        self.command_port = self.config['network']['command_port']
        self.host = self.config['network']['host_ip']

        self.logger = logging.getLogger("comm")

    def freeze(self, robot_commands = []):
        commands = grSim_Commands()
        commands.isteamyellow = False
        commands.timestamp = 0

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
        command.id = 0
        
        packet = grSim_Packet()
        packet.commands.CopyFrom(commands)

        self.command_sock.sendto(
            packet.SerializeToString(), 
            (self.host, self.command_port)
        )

    def start(self):
        self.logger.info("Starting GRSim communication...")
        self._control = self._game.control
        self.command_sock = self._create_socket()
        self.logger.info("GRSim communication module started!")
    
    def send(self):
        cmds = self._control.commands
        color = self._control.meta['color']
        self._control.new_data = False

        commands = grSim_Commands()
        commands.isteamyellow = self._get_robot_color(color)
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
        
        packet = grSim_Packet()
        packet.commands.CopyFrom(commands)

        self.command_sock.sendto(
            packet.SerializeToString(), 
            (self.host, self.command_port)
        )

    def _get_robot_color(self, team):
        return True if team == 'yellow' else False

    def _create_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
