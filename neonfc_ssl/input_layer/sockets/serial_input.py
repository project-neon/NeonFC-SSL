from serial import Serial, SerialException
from threading import Thread
from typing import TYPE_CHECKING
from ..input_data import RobotFeedback

if TYPE_CHECKING:
    from neonfc_ssl.control_layer.control_data import ControlData


class SerialInput(Thread):
    def __init__(self, config, log):
        super().__init__(daemon=True)
        self.config = config

        self.command_serial = None
        self.running = False

        # Serial Comm Parameters
        self.command_port = self.config["serial_port"]
        self.baud_rate = self.config["baud_rate"]

        # Coach Layer Logger
        self.logger = log
        self._last_data = []

    def get_data(self) -> list[RobotFeedback]:
        return [
            RobotFeedback(
                robot_id=int(robot[0]), rssi=int(robot[1]), battery=float(robot[2])
            )
            for robot in self._last_data
        ]

    def run(self):
        self.logger.info("Starting serial communication...")

        self.logger.info(f"Creating serial communication port at {self.command_port}")
        try:
            self.command_serial = Serial(self.command_port, self.baud_rate)
        except SerialException as e:
            self.logger.warning(
                f"Failed to open serial port: {self.command_port}, running without serial input"
            )
            return

        self.logger.info(f"Serial communication module started!")

        self.running = True
        try:
            self.setup_port()
            while self.running:
                try:
                    data = self.read()
                    if data is None:
                        continue

                    self._last_data = self._parse_input(data)
                except Exception as e:
                    self.logger.error(e)
        finally:
            self.close_port()
            self.logger.info("Closed feedback serial port")

    def read(self):
        return self.command_serial.readline()

    def setup_port(self):
        if not self.command_serial.is_open:
            self.command_serial.open()

    def close_port(self):
        self.clear_buffers()
        if self.command_serial.is_open:
            self.command_serial.close()

    def clear_buffers(self):
        self.command_serial.reset_input_buffer()
        self.command_serial.reset_output_buffer()

    @staticmethod
    def _parse_input(data):
        data = str(data).replace("<", "")
        return [entry.split(",") for entry in data.split(">")]

    @staticmethod
    def _validate_reading(data):
        if len(data) != 6:
            raise ValueError("Invalid data received")

        return data
