"""The sender must survive the harness not being there yet.

Before this, start() blocked for retry_attempts * retry_delay and then
raised, which killed the Decision layer's child process while the main
process carried on running.
"""

import socket
import threading
import time

from neonfc_ssl.decision_layer.drl.tcp_sender import TCPSender


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _Collector:
    """One-connection-per-accept line collector."""

    def __init__(self, port):
        self.lines = []
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # The previous collector on this port may still be unwinding.
        deadline = time.monotonic() + 5.0
        while True:
            try:
                self._sock.bind(("127.0.0.1", port))
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.05)
        self._sock.listen(1)
        self.port = port
        self._running = True
        self._conns = []
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        while self._running:
            try:
                conn, _ = self._sock.accept()
            except OSError:
                return
            self._conns.append(conn)
            threading.Thread(target=self._read, args=(conn,), daemon=True).start()

    def _read(self, conn):
        buf = b""
        with conn:
            while True:
                try:
                    chunk = conn.recv(4096)
                except OSError:
                    return
                if not chunk:
                    return
                buf += chunk
                while b"\n" in buf:
                    line, _, buf = buf.partition(b"\n")
                    self.lines.append(line.decode("utf-8"))

    def wait_for_lines(self, n, timeout=5.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and len(self.lines) < n:
            time.sleep(0.01)
        return self.lines

    def close(self):
        self._running = False
        # Closing only the listening socket leaves accepted connections
        # open, and the peer would never notice it had gone away.
        for conn in self._conns:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            conn.close()
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self._sock.close()


def test_start_returns_fast_when_no_server_is_listening():
    port = _free_port()
    sender = TCPSender("127.0.0.1", port, retry_delay=0.05)

    started = time.monotonic()
    sender.start()
    elapsed = time.monotonic() - started

    assert elapsed < 0.1
    sender.stop()


def test_payload_queued_before_the_server_existed_arrives():
    port = _free_port()
    sender = TCPSender("127.0.0.1", port, retry_delay=0.05)
    sender.start()
    sender.send({"cur_state": [0.0], "next_state": [1.0], "actions": {}})

    time.sleep(0.3)
    collector = _Collector(port)
    try:
        lines = collector.wait_for_lines(1)
    finally:
        collector.close()
        sender.stop()

    assert lines, "payload sent before the server existed never arrived"
    assert '"cur_state"' in lines[0]


def test_thread_survives_a_dropped_connection_and_reconnects():
    port = _free_port()
    sender = TCPSender("127.0.0.1", port, retry_delay=0.05, retry_attempts=3)
    sender.start()

    first = _Collector(port)
    try:
        sender.send({"n": 1})
        assert first.wait_for_lines(1)
    finally:
        first.close()

    second = _Collector(port)
    try:
        # A write to a dead peer can succeed silently for a while, so
        # keep feeding until the sender trips over it and reconnects.
        deadline = time.monotonic() + 5.0
        sent = 2
        while time.monotonic() < deadline and not second.lines:
            sender.send({"n": sent})
            sent += 1
            time.sleep(0.05)
        lines = second.wait_for_lines(1, timeout=1.0)
    finally:
        second.close()
        sender.stop()

    assert lines, "sender thread died instead of reconnecting"
