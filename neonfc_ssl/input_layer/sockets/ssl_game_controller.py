import json
import socket
import struct
import threading
import logging
from google.protobuf.json_format import MessageToJson
from neonfc_ssl.protocols.gc.ssl_gc_referee_message_pb2 import Referee
from ..input_data import GameController


class SSLGameControllerReferee(threading.Thread):
    def __init__(self, config, log):
        super(SSLGameControllerReferee, self).__init__(daemon=True)

        self.config = config

        self.running = False

        self.referee_port = self.config["game_controller_port"]
        self.host = self.config["game_controller_ip"]

        self._referee_message = {}

        self.logger = log

    def run(self):
        """Calls _create_socket() and parses the status message from the Referee."""
        self.logger.info("Starting referee module...")
        self.logger.info(f"Creating socket with address: {self.host} and port: {self.referee_port}")
        self.referee_sock = self._create_socket()
        self.logger.info("Referee module started!")

        self.running = True
        while self.running:
            c = Referee()
            data = self.referee_sock.recv(1024)
            c.ParseFromString(data)
            self._referee_message = json.loads(MessageToJson(c))
            # print(self._referee_message)
        self.stop()

    def get_data(self) -> GameController:
        return GameController(
            can_play=self.can_play(),
            state=self.get_command(),
            designated_position=self.get_designated_position(),
            team=self.get_team()
        )

    def stop(self):
        self.running = False
        self.referee_sock.close()
        self.logger.info("Referee module stopped!")

    def can_play(self):
        if not self._referee_message:
            return False

        _is_halted = self._referee_message.get('command') == 'HALT'
        _is_stopped = self._referee_message.get('command') == 'STOP'

        return not (_is_halted or _is_stopped)

    def is_stopped(self):
        return self._referee_message.get('command') == 'STOP'

    def is_halted(self):
        return self._referee_message.get('command') == 'HALT'

    def simplify(self):
        return {"command": self.get_command(), "team": self.get_team(), "pos": self.get_designated_position()}

    def get_command(self):
        return self._referee_message.get('command', "")

    def get_team(self):
        return "blue" if self._referee_message.get('command', "").endswith('BLUE') else "yellow"

    def get_designated_position(self):
        if pos := self._referee_message.get('designatedPosition', None):
            return (
                pos['x'],
                pos['y']
            )
        return None

    def get_color(self):
        return 'BLUE' if "BLUE" in self._referee_message.get('command') else 'YELLOW'

    def _create_socket(self):
        """Returns a new socket binded to the Referee."""
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
            socket.IPPROTO_UDP
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR, 1
        )

        sock.bind((self.host, self.referee_port))

        mreq = struct.pack(
            "4sl",
            socket.inet_aton(self.host),
            socket.INADDR_ANY
        )

        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            mreq
        )

        return sock
