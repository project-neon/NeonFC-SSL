from NeonPathPlanning import Point, UnivectorField
import math
from neonfc_ssl.entities import RobotCommand
from neonfc_ssl.skills.base_skill import BaseSkill
from neonfc_ssl.commons.math import reduce_ang


class MoveToPose(BaseSkill):
    def __init__(self, coach, match):
        super().__init__('MoveToPose', coach, match)

    def _start(self, target):
        self.target = target

    def decide(self):
        return RobotCommand(target_pose=self.target, robot=self._robot)

    def complete(self):
        ball = self._match.ball
        return (((self._robot.x - ball.x) ** 2 + (self._robot.y - ball.y) ** 2) ** .5) < 0.1