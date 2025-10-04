from .positional_strategy import PositionalStrategy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


BALL_SAFE_DISTANCE = 1.5
Y_MARGIN = 0.5


class PrepPenalty(PositionalStrategy):
    @staticmethod
    def decide_position(data: "MatchData", ids: list[int]):
        n_robots = len(ids)

        field = data.field
        ball = data.ball

        x = ball.x + BALL_SAFE_DISTANCE

        if n_robots == 1:
            y = field.field_width / 2
            return [(x, y)]

        y_delta = (field.field_width-2*Y_MARGIN)/(n_robots-1)
        return [(x, Y_MARGIN + i*y_delta) for i in range(n_robots)]
