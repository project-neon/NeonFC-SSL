from .custom_levels import *
from .protobuf_formatter import ProtobufFormatter
from .binary_file_handler import BinaryFileHandler

config = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "simple": {
            "format": "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
            "datefmt": "%H:%M:%S"
        },
        "protobuf": {
            "()": "neonfc_ssl.core.logger.ProtobufFormatter",
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "simple",
            "stream": "ext://sys.stderr"
        },
        "game_log": {
            "class": "neonfc_ssl.core.logger.BinaryFileHandler",
            "level": "NOTSET",
            "formatter": "protobuf",
            "path": "logs",
            "filename": "neon_fc.gamelog",
        }
    },
    "loggers": {
        "": {
            "level": "NOTSET",
        },
        "game": {
            "level": "NOTSET",
            "handlers": [
                "stdout",
                "stderr",
                "game_log"
            ],
            "propagate": False
        },
    }
}


def setup_logging():
    from logging.config import dictConfig
    dictConfig(config)
