import math
from neonfc_ssl.decision_layer.decision import RobotRubric
from .base_skill import BaseSkill


class Dribble(BaseSkill):
    def _start(self, target, avoid_area=True, avoid_allies=False, avoid_opponents=False):
        self.target = target

        self.avoid_area = avoid_area
        self.avoid_allies = avoid_allies
        self.avoid_opponents = avoid_opponents

    def decide(self, data):
        robot = data.robots[self._robot_id]
        ball = data.ball

        theta = math.atan2(robot.y - ball.y, robot.x - ball.x)

        return RobotRubric(
            id=self._robot_id,
            halt=False,
            target_pose=(self.target[0], self.target[1], theta),
            spinner=True,
            avoid_area=self.avoid_area,
            avoid_allies=[r.id for r in data.robots if r.id != self._robot_id] if self.avoid_allies else [],
            avoid_opponents=[r.id for r in data.opposites] if self.avoid_opponents else []
        )

    def complete(self, data):
        robot = data.robots[self._robot_id]
        ball = data.ball
        return (((robot.x - ball.x) ** 2 + (robot.y - ball.y) ** 2) ** .5) < 0.1
