import math
from neonfc_ssl.decision_layer.decision import RobotRubric
from .base_skill import BaseSkill


class GoToBall(BaseSkill):
    def _start(self, avoid_area=True, avoid_allies=False, avoid_opponents=False):
        self.avoid_area = avoid_area
        self.avoid_allies = avoid_allies
        self.avoid_opponents = avoid_opponents

    def decide(self, data):
        robot = data.robots[self._robot_id]
        ball = data.ball

        ttb = robot.time_to_ball(ball)
        target = ball.pos_after(ttb)

        close_to_ball = ((robot.x - target[0]) ** 2 + (robot.x - target[1]) ** 2) ** .5 < 0.15
        theta = math.atan2(-robot.y+ball.y, -robot.x+ball.x)

        return RobotRubric(
            id=self._robot_id,
            halt=False,
            target_pose=(target[0], target[1], theta),
            spinner=close_to_ball,
            avoid_area=self.avoid_area,
            avoid_allies=[r.id for r in data.robots if r.id != self._robot_id] if self.avoid_allies else [],
            avoid_opponents=[r.id for r in data.opposites] if self.avoid_opponents else []
        )

    def complete(self, data):
        robot = data.robots[self._robot_id]
        ball = data.ball

        return (((robot.x - ball.x) ** 2 + (robot.y - ball.y) ** 2) ** .5) < 0.1
