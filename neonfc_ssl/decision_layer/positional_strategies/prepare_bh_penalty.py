from .positional_strategy import PositionalStrategy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


BALL_SAFE_DISTANCE = 0.13


class PrepBHPenalty(PositionalStrategy):
    @staticmethod
    def decide_position(data: "MatchData", ids: list[int]):
        n = len(ids)
        if n != 1:
            raise ValueError("Can only decide PrepBHPlacement for 1 robot")

        ball = data.ball

        x = ball.x - BALL_SAFE_DISTANCE
        y = ball.y

        return [(x, y, 0)]
