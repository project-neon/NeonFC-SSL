import math
from neonfc_ssl.decision_layer.decision import RobotRubric
from .base_skill import BaseSkill
from ..utils import find_first_interception


class GoToBall(BaseSkill):
    def _start(self, avoid_area=True, avoid_allies=False, avoid_opponents=False):
        self.avoid_area = avoid_area
        self.avoid_allies = avoid_allies
        self.avoid_opponents = avoid_opponents

    def decide(self, data):
        robot = data.robots[self._robot_id]
        ball = data.ball

        target = find_first_interception(robot, ball)

        theta = math.atan2(-robot.y+ball.y, -robot.x+ball.x)

        return RobotRubric(
            id=self._robot_id,
            halt=False,
            target_pose=(target[0], target[1], theta),
            avoid_area=self.avoid_area,
            avoid_allies=[r.id for r in data.robots if r.id != self._robot_id] if self.avoid_allies else [],
            avoid_opponents=[r.id for r in data.opposites] if self.avoid_opponents else []
        )

    def complete(self, data):
        robot = data.robots[self._robot_id]
        ball = data.ball

        return (((robot.x - ball.x) ** 2 + (robot.y - ball.y) ** 2) ** .5) < 0.1
