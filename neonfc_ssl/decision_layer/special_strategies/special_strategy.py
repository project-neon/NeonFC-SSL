from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from neonfc_ssl.decision_layer.decision_data import RobotRubric
    from neonfc_ssl.tracking_layer.tracking_data import MatchData, TrackedRobot
    from logging import Logger


class SpecialStrategy(ABC):
    def __init__(self, logger: "Logger"):
        self._robot_id: Optional[int] = None
        self.logger = logger

    def start(self, robot_id: int, *args, **kwargs):
        self._robot_id = robot_id
        self._start(*args, **kwargs)

    def _start(self, *args, **kwargs):
        pass

    @abstractmethod
    def decide(self, data: "MatchData") -> "RobotRubric":
        pass
