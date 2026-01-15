import socket
from threading import Thread
from logging import getLogger

from .event_definitions import EventError

NEW_CONNECTION_MSG = "New connection established ({}, {})"
CONNECTION_CLOSED_MSG = "Connection closed ({}, {})"
CALLBACK_ERROR_MSG = "Error in callback: {}"
SOCKET_CLOSED_MSG = "Socket was closed"
CLIENT_HANDLER_ERROR_MSG = "Error handling client ({}, {}): {}"


class EventSocket(Thread):
    def __init__(self, host='localhost', port=0, callback=None, logger=None):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        self.running = True
        self.events = []
        self.callback = callback
        self.logger = logger if logger is not None else getLogger(__name__)
        self.client_threads = []

    def handle_client(self, client, addr):
        """Handle a persistent client connection"""
        self.logger.info(NEW_CONNECTION_MSG.format(addr[0], addr[1]))

        try:
            while self.running:
                data = client.recv(1024)
                if not data:
                    # Client closed connection
                    break

                self.events.append(data)

                # Call the callback if one is registered
                if self.callback:
                    try:
                        self.callback(data)
                    except Exception as e:
                        error_msg = CALLBACK_ERROR_MSG.format(e)
                        self.logger.error(error_msg)
                        raise EventError(error_msg) from e
        except EventError:
            # Re-raise EventError as-is
            raise
        except Exception as e:
            error_msg = CLIENT_HANDLER_ERROR_MSG.format(addr[0], addr[1], e)
            self.logger.error(error_msg)
            raise EventError(error_msg) from e
        finally:
            client.close()
            self.logger.info(CONNECTION_CLOSED_MSG.format(addr[0], addr[1]))

    def run(self):
        while self.running:
            try:
                client, addr = self.sock.accept()

                # Spawn a thread to handle this client's connection
                client_thread = Thread(target=self.handle_client, args=(client, addr))
                client_thread.daemon = True
                client_thread.start()
                self.client_threads.append(client_thread)

            except OSError:
                # Socket was closed, exit gracefully
                self.logger.debug(SOCKET_CLOSED_MSG)
                break

    def has_event(self):
        return len(self.events) > 0

    def read_event(self):
        if self.has_event():
            return self.events.pop(0)
        return None

    def set_callback(self, callback):
        """Set or update the callback function"""
        self.callback = callback

    def stop(self):
        self.running = False
        self.sock.close()

        # Wait for client threads to finish
        for thread in self.client_threads:
            thread.join(timeout=1.0)