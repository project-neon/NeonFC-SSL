from abc import ABC, abstractmethod
from neonfc_ssl.match.ssl_match import SSLMatch
from neonfc_ssl.entities import OmniRobot
from neonfc_ssl.entities import RobotCommand


class BaseStrategy(ABC):
    def __init__(self, name, coach, match: SSLMatch):
        self.name = name
        self._match = match
        self._coach = coach
        self._robot = None

    def start(self, robot: OmniRobot):
        self._robot = robot
        self._start()

    def _start(self):
        pass

    @abstractmethod
    def decide(self) -> RobotCommand:
        pass
