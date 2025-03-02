from neonfc_ssl.decision_layer.skills import *
from neonfc_ssl.decision_layer.special_strategies.special_strategy import SpecialStrategy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.match.match_data import MatchData
    from ..skills.base_skill import BaseSkill


class Still(BaseSkill):
    def _start(self):
        self.wait = Wait()
        self.wait.start(self._robot_id)

    def decide(self, data):
        return self.wait.decide(data)
