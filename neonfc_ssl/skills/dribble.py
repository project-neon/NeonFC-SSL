from NeonPathPlanning import Point, UnivectorField
import math
from neonfc_ssl.entities import RobotCommand
from neonfc_ssl.skills.base_skill import BaseSkill
from neonfc_ssl.commons.math import reduce_ang


class Dribble(BaseSkill):
    def __init__(self, coach, match):
        super().__init__('Dribble', coach, match)

    def _start(self, target):
        self.target = target

    def decide(self):
        theta = math.atan2(self._robot.y - self._match.ball.y, self._robot.x - self._match.ball.x)
        return RobotCommand(target_pose=(self.target[0], self.target[1], theta), spinner=True, robot=self._robot)

    def complete(self):
        ball = self._match.ball
        return (((self._robot.x - ball.x) ** 2 + (self._robot.y - ball.y) ** 2) ** .5) < 0.1
