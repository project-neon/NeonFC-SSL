import logging


class GameFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.last_log_time = 0
        self.refresh_rate = 1/15  # 15Hz

    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        if record.levelno != logging.getLevelName("GAME"):
            return False

        if record.msg == "frame":
            if record.created - self.last_log_time >= self.refresh_rate:
                self.last_log_time = record.created
                return True
            return False

        return True
