"""Events arriving over a real TCP socket.

recv() boundaries are arbitrary: a JSON object routinely arrives split
across two reads. The old socket handed each chunk to the parser on its
own, so a split event raised -- and took any complete events in the same
chunk down with it.
"""

import json
import socket
import threading
import time

import pytest

from neonfc_ssl.core.event import EventParser, EventSocket, EventType


def _event_dict(source="tester", event_data=None, padding=""):
    payload = {
        "type": "MasterState",
        "source": source,
        "sent_time_stamp": "2026-01-01T00:00:00.000Z",
    }
    if event_data is not None:
        payload["event_data"] = event_data
    if padding:
        payload["note"] = padding
    return json.dumps(payload)


class _SocketFixture:
    def __init__(self):
        self.received = []
        self.socket = EventSocket(host="127.0.0.1", port=0, callback=self.received.extend)
        self.socket.start()
        self.port = self.socket.sock.getsockname()[1]

    def connect(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", self.port))
        return client

    def wait(self, n, timeout=3.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and len(self.received) < n:
            time.sleep(0.01)
        return self.received

    def close(self):
        self.socket.stop()


@pytest.fixture
def fixture():
    f = _SocketFixture()
    yield f
    f.close()


def test_event_split_across_two_reads_is_delivered_once(fixture):
    raw = _event_dict().encode("utf-8")
    client = fixture.connect()
    midpoint = len(raw) // 2

    client.sendall(raw[:midpoint])
    time.sleep(0.05)
    client.sendall(raw[midpoint:])

    events = fixture.wait(1)
    client.close()

    assert len(events) == 1
    assert events[0].type == EventType.MASTER_STATE


def test_two_events_in_one_write_are_both_delivered(fixture):
    client = fixture.connect()
    client.sendall((_event_dict("a") + "\n" + _event_dict("b")).encode("utf-8"))

    events = fixture.wait(2)
    client.close()

    assert [e.source for e in events] == ["a", "b"]


def test_large_model_update_payload_is_delivered(fixture):
    models = [{"id": f"robot{i}", "file_path": "x" * 400} for i in range(10)]
    payload = json.dumps({
        "type": "ModelUpdate",
        "source": "tester",
        "sent_time_stamp": "2026-01-01T00:00:00.000Z",
        "event_data": {"models": models},
    })
    assert len(payload) > 3000

    client = fixture.connect()
    client.sendall(payload.encode("utf-8"))

    events = fixture.wait(1)
    client.close()

    assert len(events) == 1
    assert events[0].type == EventType.MODEL_UPDATE
    assert len(events[0].event_data["models"]) == 10


def test_multibyte_utf8_split_across_reads_is_delivered(fixture):
    raw = json.dumps({
        "type": "MasterState",
        "source": "tester",
        "sent_time_stamp": "2026-01-01T00:00:00.000Z",
        "event_data": {"note": "ção-ação-ação"},
    }, ensure_ascii=False).encode("utf-8")

    # Split mid-character.
    cut = raw.index(b"\xc3") + 1
    client = fixture.connect()
    client.sendall(raw[:cut])
    time.sleep(0.05)
    client.sendall(raw[cut:])

    events = fixture.wait(1)
    client.close()

    assert len(events) == 1
    assert events[0].event_data["note"] == "ção-ação-ação"


def test_parse_stream_returns_the_remainder():
    raw = _event_dict("a")
    head = (raw[:20]).encode("utf-8")

    events, remainder = EventParser.parse_stream(head.decode("utf-8"))

    assert events == []
    assert remainder == raw[:20]

    truncated = raw[:30]
    events, remainder = EventParser.parse_stream(raw + truncated)
    assert len(events) == 1
    assert events[0].source == "a"
    # The trailing half-object is held back, not raised on.
    assert remainder == truncated
