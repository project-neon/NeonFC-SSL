import math
import numpy as np
from neonfc_ssl.decision_layer.skills import GoToBall
from neonfc_ssl.decision_layer.special_strategies.special_strategy import SpecialStrategy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData
    from ..skills.base_skill import BaseSkill

def angle_between(p1, p2, p3):
    return math.atan2(p3[1] - p1[1], p3[0] - p1[0]) - math.atan2(p2[1] - p1[1], p2[0] - p1[0])


class InterceptBall(SpecialStrategy):
    def __init__(self, logger):
        super().__init__(logger)
        self.skill = GoToBall(self.logger, InterceptBall.__name__)

    def _start(self):
        self.skill.start(self._robot_id)

    def decide(self, data):
        return self.skill.decide(data)
