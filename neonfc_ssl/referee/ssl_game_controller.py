import json
import socket
import struct
import threading

from google.protobuf.json_format import MessageToJson
from neonfc_ssl.protocols.gc.ssl_gc_referee_message_pb2 import Referee


class SSLGameControllerReferee(threading.Thread):
    def __init__(self):
        super(SSLGameControllerReferee, self).__init__()
        self.referee_port = 10003
        self.host = '224.5.23.1'

        self.running = False

        self._referee_message = {}

        # logging.basicConfig(filename="GAME_CONTROLLER.log",
        #             filemode='a',
        #             format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        #             datefmt='%H:%M:%S',
        #             level=logging.DEBUG)

    def run(self):
        """Calls _create_socket() and parses the status message from the Referee."""
        print("Starting referee...")
        self.referee_sock = self._create_socket()
        print("Referee completed!")
        self.running = True
        while self.running:
            c = Referee()
            data = self.referee_sock.recv(1024)
            c.ParseFromString(data)
            self._referee_message = json.loads(MessageToJson(c))

    def stop(self):
        self.running = False

    def can_play(self):
        if not self._referee_message:
            return False

        _is_halted = self._referee_message.get('command') == 'HALT'
        _is_stopped = self._referee_message.get('command') == 'STOP'

        return not (_is_halted or _is_stopped)

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
