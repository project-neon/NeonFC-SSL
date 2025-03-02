from positional_strategy import PositionalStrategy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.match.match_data import MatchData


# TODO
class Libero(PositionalStrategy):
      
    def decide(self, data):
        pass