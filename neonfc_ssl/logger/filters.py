import logging


class OnlyGameFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return record.levelno == logging.getLevelName("GAME")
