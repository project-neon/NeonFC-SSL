from .positional_strategy import PositionalStrategy
from .full_back import FullBack
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class LeftBack(PositionalStrategy, FullBack):
    @staticmethod
    def decide(data: 'MatchData', ids: list[int]):
        return LeftBack._decide(data, ids, True)
