from abc import abstractmethod
from neonfc_ssl.algorithms.fsm import State
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..decision_data import RobotCommand
    from neonfc_ssl.tracking_layer.tracking_data import MatchData, TrackedRobot


class BaseSkill(State):
    def __init__(self):
        super().__init__()
        self._robot_id: int = None

    def start(self, robot_id: int, **kwargs):
        self._robot_id = robot_id
        self._start(**kwargs)

    def _start(self, **kwargs):
        pass

    @abstractmethod
    def decide(self, data: 'MatchData') -> 'RobotCommand':
        pass

    def complete(self, data: 'MatchData') -> bool:
        return True
