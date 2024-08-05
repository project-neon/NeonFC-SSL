from NeonPathPlanning import Point, UnivectorField
import math
from neonfc_ssl.entities import RobotCommand
from neonfc_ssl.skills.base_skill import BaseSkill
from neonfc_ssl.commons.math import reduce_ang


class GoToBall(BaseSkill):
    def __init__(self, coach, match):
        super().__init__('GoToBall', coach, match)

    def _start(self):
        self.univector = UnivectorField(n=0, rect_size=.1)
        for robot in self._match.opposites:
            self.univector.add_obstacle(robot, 0.25)

    def decide(self):
        ttb = self._robot.time_to_ball(self._match.ball)
        target = Point(*self._match.ball.pos_after(ttb))

        d = ((self._robot.x - target.x) ** 2 + (self._robot.x - target.x) ** 2) ** .5
        kp = 5
        kp_ang = 1.5

        vx = -(self._robot.x - target.x) * kp
        vx = math.copysign(min(abs(vx), 1), vx)
        vy = -(self._robot.y - target.y) * kp
        vy = math.copysign(min(abs(vy), 1), vy)
        w = reduce_ang(math.atan2(self._robot.y - self._match.ball.y, self._robot.x - self._match.ball.x) - self._robot.theta) * kp_ang

        return RobotCommand(move_speed=(vx, vy, w), spinner=d < 0.15, robot_id=self._robot.robot_id)

    def complete(self):
        ball = self._match.ball
        return (((self._robot.x - ball.x) ** 2 + (self._robot.y - ball.y) ** 2) ** .5) < 0.1
