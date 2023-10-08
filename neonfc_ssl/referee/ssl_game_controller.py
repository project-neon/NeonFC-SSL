import json
import socket
import struct
import threading

from google.protobuf.json_format import MessageToJson
from protocols.gc.ssl_gc_referee_message_pb2 import Referee


class SSLGameControllerReferee(threading.Thread):
    def __init__(self):
        super(SSLGameControllerReferee, self).__init__()
        self.referee_port = 10003
        self.host = '224.5.23.1'

        self._referee_message = None

    def run(self):
        """Calls _create_socket() and parses the status message from the Referee."""
        print("Starting referee...")
        self.referee_sock = self._create_socket()
        print("Referee completed!")
        while True:
            c = Referee()
            data = self.referee_sock.recv(1024)
            c.ParseFromString(data)
            self._referee_message = json.loads(MessageToJson(c))
            print(self._referee_message)

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