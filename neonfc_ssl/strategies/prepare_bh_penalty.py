from neonfc_ssl.skills import *
from neonfc_ssl.strategies.base_strategy import BaseStrategy
from math import atan2


class PrepBHPenalty(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('PrepBHPenalty', coach, match)

        self.active = MoveToPose(coach, match)

    def _start(self):
        self.active.start(self._robot, target=self.position())

    def decide(self):
        self.active.start(self._robot, target=self.position())
        return self.active.decide()

    def position(self):
        x = self._match.ball.x - 0.13
        y = self._match.ball.y
        theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)

        return [x, y, theta]
