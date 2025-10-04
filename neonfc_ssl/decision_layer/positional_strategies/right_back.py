from .positional_strategy import PositionalStrategy
from .full_back import FullBack
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class RightBack(PositionalStrategy, FullBack):
    @staticmethod
    def decide_position(data: 'MatchData', ids: list[int]):
        return RightBack._decide(data, ids, False)
