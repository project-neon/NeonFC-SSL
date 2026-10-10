import json
import logging
import queue
import socket
import threading
import time

_SENTINEL = object()

HOST_CONFIG_INDEX = "host"
PORT_CONFIG_INDEX = "port"
MAXSIZE_CONFIG_INDEX = "maxsize"
RETRY_ATTEMPTS_CONFIG_INDEX = "retry_attempts"
RETRY_DELAY_CONFIG_INDEX = "retry_delay"

# Log the "still can't reach the peer" message this often instead of on
# every single attempt, which at retry_delay=1.0 would be one line/second.
CONNECT_LOG_EVERY = 10


class TCPSender:
    """Non-blocking TCP sender that runs a dedicated sender thread.

    The coach calls `send()` which enqueues the payload and returns
    immediately.  A background thread drains the queue and handles all
    I/O, reconnection, and retries — the coach is never blocked.

    Connection handling is deliberately forgiving: `start()` returns
    immediately whether or not the peer is listening, and the sender
    thread keeps trying until it is.  A harness that isn't up yet must
    not take the decision layer down with it.

    Args:
        host:            Remote host to connect to.
        port:            Remote port to connect to.
        maxsize:         Maximum queue depth.  If the queue is full when
                         `send()` is called, an error is logged and the
                         payload is dropped (back-log protection).
        retry_attempts:  How many times to retry a failed *send* before
                         giving up on that payload.
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

        # Looked up here rather than at import time: setup_logging() runs
        # dictConfig(disable_existing_loggers=True) *after* this module is
        # imported, which silences a module-level logger for the rest of
        # the process.
        self.__logger = logging.getLogger(__name__)
        self.__logger.disabled = False

        self.__queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self.__socket: socket.socket | None = None
        self.__stopping = threading.Event()
        self.__thread = threading.Thread(target=self.__run, daemon=True, name="TCPSender")

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def start(self):
        """Start the background sender thread.  Does not connect."""
        self.__thread.start()

    def stop(self):
        """Signal shutdown, drain the queue, and join the thread."""
        self.__stopping.set()
        try:
            self.__queue.put_nowait(_SENTINEL)
        except queue.Full:
            self.__logger.warning("TCPSender queue full at shutdown; thread will exit when drained")
        if self.__thread.is_alive():
            self.__thread.join(timeout=5.0)
        self.__close_socket()

    def send(self, payload: dict):
        """Enqueue a payload for sending.  Never blocks the caller.

        Raises a logged error (without raising an exception to the coach)
        if the queue is full.
        """
        try:
            self.__queue.put_nowait(payload)
        except queue.Full:
            self.__logger.error(
                "TCPSender queue is full (%d slots) — dropping payload: %s",
                self.__queue.maxsize,
                payload,
            )

    # ------------------------------------------------------------------ #
    # Background thread                                                    #
    # ------------------------------------------------------------------ #

    def __run(self):
        """Nothing raised in here is allowed to kill the thread: a dead
        sender silently drops every transition from then on, and the
        coach has no way to tell."""
        while True:
            payload = self.__queue.get()

            if payload is _SENTINEL:
                break

            try:
                message = (json.dumps(payload) + "\n").encode("utf-8")
                if self.__socket is None and not self.__connect_forever():
                    break
                self.__send_with_retry(message)
            except Exception:
                self.__logger.exception("TCPSender: dropping payload after an unexpected error")

        self.__close_socket()

    def __send_with_retry(self, message: bytes):
        """Sends one message, reconnecting between attempts.

        Bounded by retry_attempts: a payload that keeps failing is
        dropped rather than blocking the queue behind it.
        """
        for attempt in range(1, self.__retry_attempts + 1):
            try:
                self.__socket.sendall(message)
                return
            except (BrokenPipeError, OSError) as exc:
                self.__logger.warning(
                    "TCPSender send failed (attempt %d/%d): %s — reconnecting…",
                    attempt,
                    self.__retry_attempts,
                    exc,
                )
                if not self.__reconnect_once():
                    return

        self.__logger.error(
            "TCPSender gave up after %d attempts — dropping message.",
            self.__retry_attempts,
        )

    # ------------------------------------------------------------------ #
    # Connection management                                                #
    # ------------------------------------------------------------------ #

    def __connect_forever(self) -> bool:
        """Retries until connected.  Returns False if asked to stop."""
        attempts = 0
        while not self.__stopping.is_set():
            attempts += 1
            sock = self.__try_connect(attempts)
            if sock is not None:
                self.__socket = sock
                self.__logger.info(
                    "TCPSender connected to %s:%d (after %d attempt(s))",
                    self.__host, self.__port, attempts,
                )
                return True
            if self.__stopping.wait(self.__retry_delay):
                return False
        return False

    def __reconnect_once(self) -> bool:
        """A single reconnect attempt, for use inside the per-message
        retry loop. Returns True if we're connected again."""
        self.__close_socket()
        if self.__stopping.wait(self.__retry_delay):
            return False
        sock = self.__try_connect(1)
        if sock is None:
            return False
        self.__socket = sock
        return True

    def __try_connect(self, attempt: int) -> socket.socket | None:
        """One connection attempt.  Never raises -- connection failures
        are an expected steady state, not an error."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.__host, self.__port))
            return sock
        except OSError as exc:
            # Throttled so an unreachable peer costs one line every
            # CONNECT_LOG_EVERY attempts, not one per retry_delay.
            if attempt == 1 or attempt % CONNECT_LOG_EVERY == 0:
                self.__logger.warning(
                    "TCPSender connection attempt %d to %s:%d failed: %s",
                    attempt, self.__host, self.__port, exc,
                )
            return None

    def __close_socket(self):
        if self.__socket is not None:
            try:
                self.__socket.close()
            except OSError:
                pass
            self.__socket = None
