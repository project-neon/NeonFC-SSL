from neonfc_ssl.decision_layer.skills import *
from neonfc_ssl.decision_layer.special_strategies.special_strategy import SpecialStrategy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class Still(SpecialStrategy):
    def _start(self):
        self.wait = Wait(self.logger, Still.__name__)
        self.wait.start(self._robot_id)

    def decide(self, data):
        return self.wait.decide(data)
