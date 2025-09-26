from abc import abstractmethod
from neonfc_ssl.algorithms.fsm import State
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..decision_data import RobotRubric
    from neonfc_ssl.tracking_layer.tracking_data import MatchData, TrackedRobot
    from logging import Logger


class BaseSkill(State):
    def __init__(self, logger: "Logger", strategy_name: str):
        super().__init__()
        self.logger = logger
        self.strategy_name = strategy_name
        self._robot_id: Optional[int] = None

    def start(self, robot_id: int, **kwargs):
        self._robot_id = robot_id
        self._start(**kwargs)

    def _start(self, **kwargs):
        pass

    @abstractmethod
    def decide(self, data: "MatchData") -> "RobotRubric":
        pass

    def complete(self, data: "MatchData") -> bool:
        return True
