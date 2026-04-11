from math import atan2
from .positional_strategy import PositionalStrategy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class PrepKickoff(PositionalStrategy):
    @staticmethod
    def decide_position(data: "MatchData", ids: list[int]):
        n = len(ids)
        if n != 1:
            raise ValueError("Can only decide PrepKickoff for 1 robot")

        robot = data.robots[ids[0]]
        ball = data.ball
        field = data.field
        friendly = data.game_state.friendly

        if friendly:
            x = field.field_length/2 - 0.3

        else:
            x = field.field_length/2 - 0.6

        y = field.field_width/2
        theta = atan2(-robot.y + ball.y, -robot.x + ball.x)

        return [(x, y, theta)]
