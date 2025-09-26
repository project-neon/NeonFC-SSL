from itertools import chain, pairwise
from neonfc_ssl.commons.math import point_in_triangle
from .base_skill import BaseSkill
from .passing import SimplePass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData, TrackedRobot, TrackedBall


class Shoot(BaseSkill):
    def __init__(self, logger, strategy):
        super().__init__(logger, strategy)
        self.target = None

    def _start(self, **kwargs):
        self.skill = SimplePass(self.logger, self.strategy_name, override_kick=6.5)
        self.target = None

    def decide(self, data):
        if self.target is None:
            self.target = self.find_best_shoot(data)
            self.skill.start(self._robot_id, target=self.target)

        return self.skill.decide(data)

    @staticmethod
    def find_best_shoot(data: "MatchData"):
        ball = data.ball
        goal_posts = ((9, 2.5), (9, 3.5))

        obstacles = filter(
            lambda r: point_in_triangle(r, ball, goal_posts[0], goal_posts[1]),
            data.opposites.actives,
        )

        def project_on_goal(robot):
            alpha = data.field.field_length - ball.x
            beta = data.field.field_length - robot.x

            return (alpha * robot.x - beta * ball.y) / (alpha - beta)

        obstacles_proj = sorted(
            chain(map(project_on_goal, obstacles), map(lambda g: g[1], goal_posts))
        )
        max_gap = max(pairwise(obstacles_proj), key=lambda x: x[1] - x[0])
        target = max_gap[0] + (max_gap[1] - max_gap[0]) / 2

        return data.field.field_length, target

    @staticmethod
    def start_shoot(robot: "TrackedRobot", ball: "TrackedBall", **kwargs):
        return SimplePass.start_pass(robot, ball, **kwargs)

    @staticmethod
    def stop_shoot(robot: "TrackedRobot", ball: "TrackedBall", **kwargs):
        return SimplePass.stop_pass(robot, ball, **kwargs)
