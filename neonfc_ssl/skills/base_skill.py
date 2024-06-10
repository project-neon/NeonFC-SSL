from abc import abstractmethod
from neonfc_ssl.algorithms.fsm import State
from neonfc_ssl.entities import RobotCommand


class BaseSkill(State):
    def __init__(self, name, coach, match):
        super().__init__()
        self.name = name
        self._coach = coach
        self._match = match
        self._robot = None

    def start(self, robot, **kwargs):
        self._robot = robot
        self._start(**kwargs)

    def _start(self, **kwargs):
        pass

    @abstractmethod
    def decide(self) -> RobotCommand:
        pass
