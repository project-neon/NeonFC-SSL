import socket

from protocols.grSim.grSim_Commands_pb2 import grSim_Commands
from protocols.grSim.grSim_Packet_pb2 import grSim_Packet

class GrComm(object):
    def __init__(self):
        super(GrComm, self).__init__()

        self.commands = []

        self.command_port = 20011
        self.host = 'localhost'

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
        print("Starting communication...")
        self.command_sock = self._create_socket()
        print("Communication socket created!")
    
    def send(self, robot_commands = []):
        '''
        Send commands to GrSim

        robot_commands follows:
        [
            {
                robot_id: NUM,
                color: 'yellow|blue',
                wheel_1: float,
                wheel_2: float,
                wheel_3: float,
                wheel_4: float,
            }
        ]
        '''
        commands = grSim_Commands()
        commands.isteamyellow = self._get_robot_color(robot_commands[0])
        commands.timestamp = 0
        for robot in robot_commands:
            command = commands.robot_commands.add()
            command.wheel1 = robot['wheel_1']
            command.wheel2 = robot['wheel_2']
            command.wheel3 = robot['wheel_3']
            command.wheel4 = robot['wheel_4']
            command.kickspeedx = 0
            command.kickspeedz = 0
            command.veltangent = 0
            command.velnormal = 0
            command.velangular = 0
            command.spinner = False
            command.wheelsspeed = True
            command.id = robot['robot_id']
        
        packet = grSim_Packet()
        packet.commands.CopyFrom(commands)

        self.command_sock.sendto(
            packet.SerializeToString(), 
            (self.host, self.command_port)
        )

    def _get_robot_color(self, robot):
        return True if robot['color'] == 'YELLOW' else False
    
    def _create_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)