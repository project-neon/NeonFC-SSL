import datetime as dt
import json
import logging

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
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


# source https://github.com/mCodingLLC/VideosSampleCode/tree/master/videos/135_modern_logging
class JSONLFormatter(logging.Formatter):
    def __init__(
        self,
        *,
        fmt_keys: dict[str, str] | None = None,
        datefmt: str | None = None
    ):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}
        self.datefmt = datefmt

    def format(self, record: logging.LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str, separators=(',', ':'))

    def _prepare_log_dict(self, record: logging.LogRecord):
        if self.datefmt is None:
            tmstp = dt.datetime.fromtimestamp(record.created).isoformat()
        else:
            tmstp = dt.datetime.fromtimestamp(record.created).strftime(self.datefmt)

        always_fields = {
            "message": record.getMessage(),
            "timestamp": tmstp,
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: msg_val
            if (msg_val := always_fields.pop(val, None)) is not None
            else getattr(record, val)
            for key, val in self.fmt_keys.items()
        }
        message.update(always_fields)

        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val

        return message
