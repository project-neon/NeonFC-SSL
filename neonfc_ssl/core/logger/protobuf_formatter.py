import datetime as dt
import json
from google.protobuf.message import Message
from google.protobuf.timestamp_pb2 import Timestamp
import logging
from .custom_levels import LEVELS
from neonfc_ssl.protocols.internal import NeonFCProtobuf
import neonfc_ssl.protocols.internal as protocols

LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "nTRACKINGame",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class ProtobufFormatter(logging.Formatter):
    def __init__(
        self,
        *_
    ):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        entry = NeonFCProtobuf.LogEntry(
            timestamp=Timestamp().FromDatetime(dt.datetime.fromtimestamp(record.created)),
            source=NeonFCProtobuf.Sources.Value(record.name.upper()),
            level=record.levelno,
        )

        if isinstance(record.msg, Message):
            if record.levelno in LEVELS:
                setattr(entry, record.levelname.upper(), record.msg)
            else:
                raise ValueError(f"Unknow level {record.levelname}, with value {record.levelno}")

        if isinstance(record.msg, str):
            entry.message = record.msg

        return entry.SerializeToString()
