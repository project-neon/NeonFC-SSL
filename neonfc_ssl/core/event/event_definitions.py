import enum
from dataclasses import dataclass
from datetime import datetime


class EventType(enum.Enum):
    MASTER_STATE = "MasterState"
    MODEL_UPDATE = "ModelUpdate"


@dataclass(frozen=True)
class Event:
    type: EventType
    source: str
    sent_time_stamp: datetime
    event_data: dict | None = None


class EventError(Exception):
    pass
