from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..decision import Decision
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class Coach(ABC):
    def __init__(self, decision: 'Decision'):
        self.decision = decision
        self.data: 'MatchData'
        self._start()

    def _start(self):
        pass

    @abstractmethod
    def decide(self):
        """This function decides which strategy each robot will use based on the current match data.

        For setting hungarian robots use the self.decision.calculate_hungarian method
        For setting special robots use the self.decision.set_strategy method
        Active robots that are not set thru neither of these will keep using the last set strategy or will remain
        still if no strategy was ever set
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    def __call__(self, data: 'MatchData'):
        """Set the last data and call the decide method."""
        self.data = data
        self.decide()

    def has_possession(self):
        """Check if the team has possession of the ball."""
        return self.data.possession.possession_team == "yellow" != self.data.is_yellow
