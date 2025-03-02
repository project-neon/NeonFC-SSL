from NeonPathPlanning.potential_fields import PotentialField, PointField, LineField
import logging
from neonfc_ssl.entities import RobotCommand
from neonfc_ssl.decision_layer.special_strategies import BaseStrategy
import math
from neonfc_ssl.decision_layer.skills import *
from neonfc_ssl.decision_layer.special_strategies.special_strategy import SpecialStrategy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.match.match_data import MatchData
    from neonfc_ssl.decision_layer.skills.base_skill import BaseSkill



class Receiver(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('SoloAttacker', coach, match)
        self.field = None

    def _start(self):
        self.field = PotentialField(self._match)

        D = 4  # m
        L = 1

        def locate_robot(r):
            return lambda x: (r.x, r.y) if not r.missing else (-10, -10)

        def ang_robot_ball(r):
            return lambda m: math.pi - math.atan2(r.y-m.ball.y, r.x-m.ball.x)

        for r in self._match.robots:
            if r == self._robot:
                continue
            self.field.add_field(PointField(
                self._match,
                target=locate_robot(r),
                radius_max=2,
                decay=lambda x: 1/x,
                multiplier=-0.5  # 50 cm/s
            ))

        for r in self._match.opposites:
            self.field.add_field(PointField(
                self._match,
                target=locate_robot(r),
                radius_max=0.3,  # 25 cm
                decay=lambda x: 1,
                multiplier=-1  # 50 cm/s
            ))
            self.field.add_field(LineField(
                self._match,
                target=locate_robot(r),
                theta=ang_robot_ball(r),
                inverse=True,
                line_size_single_side=True,
                line_size=D,
                multiplier=-1,
                decay=lambda x: 1,
                line_dist=L,
                line_dist_max=L
            ))

    def decide(self):
        vx, vy = self.field.compute([self._robot.x, self._robot.y])

        return RobotCommand(move_speed=(vx, vy, 0), robot=self._robot)
