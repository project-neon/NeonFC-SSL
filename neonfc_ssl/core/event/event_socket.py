import codecs
import socket
from threading import Thread
from logging import getLogger

from .event_definitions import EventError
from .event_parser import EventParser

NEW_CONNECTION_MSG = "New connection established ({}, {})"
CONNECTION_CLOSED_MSG = "Connection closed ({}, {})"
CALLBACK_ERROR_MSG = "Error in callback: {}"
SOCKET_CLOSED_MSG = "Socket was closed"
CLIENT_HANDLER_ERROR_MSG = "Error handling client ({}, {}): {}"
PENDING_TOO_LARGE_MSG = (
    "Discarding {} unparsed bytes from {} -- no complete JSON object in that much data"
)


class EventSocket(Thread):
    # A connection that has buffered this much without producing one
    # complete JSON object is not sending events; drop the buffer rather
    # than let it grow forever.
    MAX_PENDING = 1_000_000

    def __init__(self, host='localhost', port=0, callback=None, logger=None):
        super().__init__(daemon=True)
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
        """Handle a persistent client connection.

        Bytes are buffered per connection: a recv() boundary means nothing
        about JSON object boundaries, so anything that doesn't parse yet is
        held until the rest of it arrives.
        """
        self.logger.info(NEW_CONNECTION_MSG.format(addr[0], addr[1]))

        # Incremental decoder so a multi-byte UTF-8 character split across
        # two recv() calls doesn't decode to garbage.
        decoder = codecs.getincrementaldecoder('utf-8')()
        pending = ''

        try:
            while self.running:
                data = client.recv(1024)
                if not data:
                    # Client closed connection
                    break

                pending += decoder.decode(data)

                try:
                    events, pending = EventParser.parse_stream(pending)
                except EventError as e:
                    # A malformed complete object: drop the buffer rather
                    # than resync from a known-bad offset, and keep the
                    # connection so later events still land.
                    self.logger.error(CALLBACK_ERROR_MSG.format(e))
                    pending = ''
                    continue

                if len(pending) > self.MAX_PENDING:
                    self.logger.error(
                        PENDING_TOO_LARGE_MSG.format(len(pending), addr)
                    )
                    pending = ''

                if not events:
                    continue

                # Only buffered when nobody is listening, so `events`
                # can't grow without bound during normal operation.
                if self.callback:
                    try:
                        self.callback(events)
                    except Exception as e:
                        # Never let a callback failure kill the connection.
                        self.logger.error(CALLBACK_ERROR_MSG.format(e))
                else:
                    self.events.extend(events)
        except OSError as e:
            self.logger.error(CLIENT_HANDLER_ERROR_MSG.format(addr[0], addr[1], e))
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
        """Set or update the callback function.

        It receives a list of already-parsed Events.
        """
        self.callback = callback

    def stop(self):
        self.running = False
        self.sock.close()

        # Wait for client threads to finish
        for thread in self.client_threads:
            thread.join(timeout=1.0)
