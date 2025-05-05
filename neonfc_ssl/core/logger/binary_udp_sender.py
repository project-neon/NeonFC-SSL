import logging
import socket


class BinaryUDPSender(logging.Handler):
    def __init__(self, host: str, port: int):
        super().__init__()
        self.address = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def emit(self, record):
        try:
            msg = self.format(record)
            if isinstance(msg, str):
                msg = msg.encode("utf-8")  # Only if your formatter returns strings
            self.sock.sendto(msg, self.address)

        except Exception:
            self.handleError(record)

    def close(self):
        try:
            self.sock.close()
        finally:
            super().close()
