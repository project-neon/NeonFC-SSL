from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.decision_layer.decision_data import RobotRubric
    from neonfc_ssl.tracking_layer.tracking_data import MatchData, TrackedRobot


class SpecialStrategy(ABC):
    def __init__(self):
        self._robot_id = None

    def start(self, robot_id: int, *args, **kwargs):
        self._robot_id = robot_id
        self._start(*args, **kwargs)

    def _start(self, *args, **kwargs):
        pass

    @abstractmethod
    def decide(self, data: 'MatchData') -> 'RobotRubric':
        pass
