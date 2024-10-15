import logging
import serial
from neonfc_ssl.control import Control


class SerialComm:
    def __init__(self, game):
        self._game = game
        self._config = self._game.config

        # Control Layer Class
        self._control: Control = None

        # Serial Comm Classes
        self.commands = []
        self.command_sock = None

        # Serial Comm Parameters
        self.command_port = self._config["serial"]["command_port"]
        self.baud_rate = self._config["serial"]["baud_rate"]

        # Coach Layer Logger
        self.logger = logging.getLogger("comm")

    def start(self):
        self.logger.info("Starting serial communication...")

        self._control = self._game.control

        self.logger.info(f"Creating serial communication port at {self.command_port}")
        self.comm = serial.Serial(self.command_port, self.baud_rate)

        self.logger.info(f"Serial communication module started!")
    
    def freeze(self):
        message = "<"

        for robot in self._config['match']['robots_ids']:
            message += f"{robot},{round(0, 4)},{round(0, 4)},{round(0, 4)}"

        message = message[:-1] + '>'

    def update(self):
        cmds = self._control.commands
        self._control.new_data = False

        message = "<"
        for robot in cmds:
            robot.global_speed_to_local_speed()
            message += (
                f"{robot.robot.robot_id},"
                f"{round(robot.local_speed[0], 4)},"
                f"{round(robot.local_speed[1], 4)},"
                f"{round(robot.local_speed[2], 4)},"
            )

        message = message[:-1] + '>'

        self.send(message)

    def send(self, message):
        self.comm.write(message.encode())
