import json
import logging
import queue
import socket
import threading
import time

logger = logging.getLogger(__name__)

_SENTINEL = object()

HOST_CONFIG_INDEX = "host"
PORT_CONFIG_INDEX = "port"
MAXSIZE_CONFIG_INDEX = "maxsize"
RETRY_ATTEMPTS_CONFIG_INDEX = "retry_attempts"
RETRY_DELAY_CONFIG_INDEX = "retry_delay"


class TCPSender:
    """Non-blocking TCP sender that runs a dedicated sender thread.

    The coach calls `send()` which enqueues the payload and returns
    immediately.  A background thread drains the queue and handles all
    I/O, reconnection, and retries — the coach is never blocked.

    Args:
        host:            Remote host to connect to.
        port:            Remote port to connect to.
        maxsize:         Maximum queue depth.  If the queue is full when
                         `send()` is called, an error is logged and the
                         payload is dropped (back-log protection).
        retry_attempts:  How many times to retry a failed connection
                         before giving up on that payload.
        retry_delay:     Seconds to wait between reconnection attempts.
    """

    @classmethod
    def from_config(cls, config):
        optional = (MAXSIZE_CONFIG_INDEX, RETRY_ATTEMPTS_CONFIG_INDEX, RETRY_DELAY_CONFIG_INDEX)
        return cls(
            host=config[HOST_CONFIG_INDEX],
            port=config[PORT_CONFIG_INDEX],
            **{k: config[k] for k in optional if k in config}
        )

    def __init__(
        self,
        host: str,
        port: int,
        maxsize: int = 64,
        retry_attempts: int = 5,
        retry_delay: float = 1.0,
    ):
        self.__host = host
        self.__port = port
        self.__retry_attempts = retry_attempts
        self.__retry_delay = retry_delay

        self.__queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self.__socket: socket.socket | None = None
        self.__thread = threading.Thread(target=self.__run, daemon=True, name="TCPSender")

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def start(self):
        """Connect and start the background sender thread."""
        self.__connect()
        self.__thread.start()

    def stop(self):
        """Drain the queue and shut down cleanly."""
        self.__queue.put(_SENTINEL)
        self.__thread.join()
        if self.__socket:
            self.__socket.close()
            self.__socket = None

    def send(self, payload: dict):
        """Enqueue a payload for sending.  Never blocks the caller.

        Raises a logged error (without raising an exception to the coach)
        if the queue is full.
        """
        try:
            self.__queue.put_nowait(payload)
        except queue.Full:
            logger.error(
                "TCPSender queue is full (%d slots) — dropping payload: %s",
                self.__queue.maxsize,
                payload,
            )

    # ------------------------------------------------------------------ #
    # Background thread                                                    #
    # ------------------------------------------------------------------ #

    def __run(self):
        while True:
            payload = self.__queue.get()

            if payload is _SENTINEL:
                break

            message = (json.dumps(payload) + "\n").encode("utf-8")
            self.__send_with_retry(message)

    def __send_with_retry(self, message: bytes):
        for attempt in range(1, self.__retry_attempts + 1):
            try:
                self.__socket.sendall(message)
                return
            except (BrokenPipeError, OSError) as exc:
                logger.warning(
                    "TCPSender send failed (attempt %d/%d): %s — reconnecting…",
                    attempt,
                    self.__retry_attempts,
                    exc,
                )
                self.__reconnect()

        logger.error(
            "TCPSender gave up after %d attempts — dropping message.",
            self.__retry_attempts,
        )

    # ------------------------------------------------------------------ #
    # Connection management                                                #
    # ------------------------------------------------------------------ #

    def __connect(self):
        for attempt in range(1, self.__retry_attempts + 1):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.__host, self.__port))
                self.__socket = sock
                logger.info("TCPSender connected to %s:%d", self.__host, self.__port)
                return
            except OSError as exc:
                logger.warning(
                    "TCPSender connection attempt %d/%d failed: %s",
                    attempt,
                    self.__retry_attempts,
                    exc,
                )
                time.sleep(self.__retry_delay)

        raise ConnectionError(
            f"TCPSender could not connect to {self.__host}:{self.__port} "
            f"after {self.__retry_attempts} attempts."
        )

    def __reconnect(self):
        if self.__socket:
            try:
                self.__socket.close()
            except OSError:
                pass
            self.__socket = None
        time.sleep(self.__retry_delay)
        self.__connect()