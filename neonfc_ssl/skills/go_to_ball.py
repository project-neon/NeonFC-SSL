from NeonPathPlanning import Point, UnivectorField
import math
from neonfc_ssl.entities import RobotCommand
from neonfc_ssl.skills.base_skill import BaseSkill
from neonfc_ssl.commons.math import reduce_ang


class GoToBall(BaseSkill):
    def __init__(self, coach, match):
        super().__init__('GoToBall', coach, match)

    def decide(self):
        ttb = self._robot.time_to_ball(self._match.ball)
        target = self._match.ball.pos_after(ttb)

        close_to_ball = ((self._robot.x - target[0]) ** 2 + (self._robot.x - target[1]) ** 2) ** .5 < 0.15
        theta = math.atan2(self._robot.y - self._match.ball.y, self._robot.x - self._match.ball.x)

        return RobotCommand(target_pose=(target[0], target[1], theta), spinner=close_to_ball, robot=self._robot)

    def complete(self):
        ball = self._match.ball
        return (((self._robot.x - ball.x) ** 2 + (self._robot.y - ball.y) ** 2) ** .5) < 0.1
