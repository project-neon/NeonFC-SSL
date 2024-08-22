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
        self.univector = UnivectorField(n=0, rect_size=.1)
        for robot in self._match.opposites:
            self.univector.add_obstacle(robot, 0.25)

    def decide(self):
        target = Point(*self.target)
        kp = 10
        kp_ang = 1.5

        vx = -(self._robot.x - target.x) * kp
        vx = math.copysign(min(abs(vx), 1), vx)
        vy = -(self._robot.y - target.y) * kp
        vy = math.copysign(min(abs(vy), 1), vy)

        w = reduce_ang(math.atan2(self._robot.y - self._match.ball.y, self._robot.x - self._match.ball.x) - self._robot.theta) * kp_ang

        return RobotCommand(move_speed=(vx, vy, w), spinner=True, robot_id=self._robot.robot_id)

    def complete(self):
        ball = self._match.ball
        return (((self._robot.x - ball.x) ** 2 + (self._robot.y - ball.y) ** 2) ** .5) < 0.1
