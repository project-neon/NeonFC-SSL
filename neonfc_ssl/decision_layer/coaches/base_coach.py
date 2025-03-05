from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..decision import Decision
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class Coach(ABC):
    def __init__(self, decision: 'Decision'):
        self.decision = decision
        self._start()

    def _start(self):
        pass

    @abstractmethod
    def __call__(self, data: 'MatchData'):
        """This function takes the info about the game and decides which strategy each robot will use

        For setting hungarian robots use the self.decision.calculate_hungarian method
        For setting special robots use the self.decision.set_strategy method
        Active robots that are not set thru neither of these will keep using the last set strategy or will remain
        still if no strategy was ever set
        """
        pass
