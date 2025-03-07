import logging
from serial import Serial

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.control_layer.control_data import ControlData


class SerialComm:
    def __init__(self, config, log):
        self.config = config

        self.command_serial = None

        # Serial Comm Parameters
        self.command_port = self.config["command_port"]
        self.baud_rate = self.config["baud_rate"]

        # Coach Layer Logger
        self.logger = log

    def start(self):
        self.logger(logging.INFO, "Starting serial communication...")

        self.logger.info(f"Creating serial communication port at {self.command_port}")
        self.command_serial = Serial(self.command_port, self.baud_rate)

        self.logger(logging.INFO, f"Serial communication module started!")

    def update(self, data: 'ControlData'):
        message = "<"
        for cmd in data.commands:
            message += (
                f"{cmd.id},"
                f"{round(cmd.vel_tangent, 2)},"
                f"{round(cmd.vel_normal, 2)},"
                f"{round(cmd.vel_angular, 2)},"
                # f"{0 if abs(cmd.kick_x) < 0.05 else 9},"
            )

        message = message[:-1] + '>'

        self.send(message)

    def send(self, message):
        self.command_serial.write(message.encode())
