import socket
from neonfc_ssl.protocols.sim.ssl_simulation_robot_control_pb2 import RobotControl

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.control_layer.control_data import ControlData


class SimCliComm:
    def __init__(self, config, log):
        self.config = config
        self.logger = log

        self.command_sock = None

        self.command_port = self.config['command_port']
        self.host = self.config['host_ip']

    def start(self):
        self.logger.info("Starting SSL Simulation communication...")
        self.logger.info(f"Creating socket with address: {self.host} and port: {self.command_port}")
        self.command_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger.info("SSL Simulation communication module started!")
    
    def update(self, cmds: 'ControlData'):
        if not cmds.commands:
            return

        control = RobotControl()

        for cmd in cmds.commands:
            rubric = control.robot_commands.add()
            rubric.id = cmd.id
            rubric.kick_speed = min(cmd.kick_x, 2)
            
            # Using Local Velocity
            move_cmd = rubric.move_command
            local_vel = move_cmd.local_velocity
            local_vel.forward = cmd.vel_tangent
            local_vel.left = cmd.vel_normal
            local_vel.angular = cmd.vel_angular

        self.send(control)

    def send(self, control: RobotControl):
        self.command_sock.sendto(
            control.SerializeToString(),
            (self.host, self.command_port)
        )
