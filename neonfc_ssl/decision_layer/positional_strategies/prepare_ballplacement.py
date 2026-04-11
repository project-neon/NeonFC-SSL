from math import atan2
from .positional_strategy import PositionalStrategy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class PrepBallPlacement(PositionalStrategy):
    @staticmethod
    def decide_position(data: "MatchData", ids: list[int]):
        n = len(ids)
        if n != 1:
            raise Exception(f"Can only decide PrepBallPlacement for 1 robot: {ids}")

        robot = data.robots[ids[0]]
        ball = data.ball
        field = data.field
        friendly = data.game_state.friendly
        foul_pos = data.ball

        if friendly:
            x = foul_pos[0] - 0.5
            y = foul_pos[1]

        else:
            if foul_pos[0] < field.field_width/2:
                x = foul_pos[0] - 0.7
                y = foul_pos[1] + 0.7

            else:
                x = foul_pos[0] - 0.7
                y = foul_pos[1] - 0.7

        theta = atan2(-robot.y + ball.y, -robot.x + ball.x)

        return [(x, y, theta)]
