import logging
import os
import serial
import json


class SerialComm(object):
    def __init__(self):
        super(SerialComm, self).__init__()
        self.commands = []
        self.command_port = "/dev/ttyACM0"
        self.baud_rate = 115200

        self.logger = logging.getLogger("comm")

    def start(self):
        self.logger.info("Starting serial communication...")
        self.logger.info(f"Creating communication port at {self.command_port}")
        self.comm = serial.Serial(self.command_port, self.baud_rate)
        self.logger.info(f"Serial communication module started!")
    
    def freeze(self, robot_commands = []):
        message = "<"
        robot_commands = sorted(robot_commands, key = lambda i: i['robot_id'])
        for rb in robot_commands:
            message += f"{rb['robot_id']},{round(0, 4)},{round(0, 4)},{round(rb['actual_theta'], 4)}"

        message = message[:-1] + '>'
        self.comm.write(message.encode())

    def send(self, robot_commands = []):
        '''
        Send commands to ESP-32

        robot_commands follows:
        [
            {
                robot_id: int,
                color: 'yellow|blue',
                vx: float,
                vy: float,
                can_kick: bool,
                actual_theta: float
                
            }
        ]
        '''
        message = "<"
        robot_commands = sorted(robot_commands, key = lambda i: i['robot_id'])
        for rb in robot_commands:
            message += f"{rb['robot_id']},{round(rb['vx'], 4)},{round(rb['vy'], 4)},{round(rb['actual_theta'], 4)}"

        message = message[:-1] + '>'

        self.comm.write(message.encode())

    def _get_robot_color(self, robot):
        return True if robot['color'] == 'yellow' else False