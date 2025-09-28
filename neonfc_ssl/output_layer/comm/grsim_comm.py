import logging
import socket
from neonfc_ssl.protocols.grSim.grSim_Commands_pb2 import grSim_Commands
from neonfc_ssl.protocols.grSim.grSim_Packet_pb2 import grSim_Packet

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.control_layer.control_data import ControlData


class GrComm:
    def __init__(self, config, log):
        self.config = config
        self.logger = log

        # GrSim Comm Classes
        self.command_sock = None

        # GrSim Comm Parameters
        self.command_port = self.config['command_port']
        self.host = self.config['host_ip']

    def start(self):
        self.logger.info("Starting GRSim communication...")

        self.logger.info(f"Creating socket with address: {self.host} and port: {self.command_port}")
        self.command_sock = self._create_socket()

        self.logger.info("GRSim communication module started!")
    
    def update(self, cmds: 'ControlData'):
        if not cmds.commands:
            return

        commands = grSim_Commands()
        commands.isteamyellow = cmds.commands[0].is_yellow
        commands.timestamp = 0

        for cmd in cmds.commands:
            # robot.global_speed_to_wheel_speed()
            command = commands.robot_commands.add()
            command.wheel1 = 0
            command.wheel2 = 0
            command.wheel3 = 0
            command.wheel4 = 0
            command.kickspeedx = min(cmd.kick_x, 2)
            command.kickspeedz = 0 # cmd.kick_z
            command.veltangent = cmd.vel_tangent
            command.velnormal = cmd.vel_normal
            command.velangular = cmd.vel_angular
            command.spinner = cmd.spinner
            command.wheelsspeed = False
            command.id = cmd.id

        self.send(commands)

    def send(self, commands):
        packet = grSim_Packet()
        packet.commands.CopyFrom(commands)

        self.command_sock.sendto(
            packet.SerializeToString(),
            (self.host, self.command_port)
        )

    @staticmethod
    def _create_socket():
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
