from math import atan2
from .positional_strategy import PositionalStrategy


class PrepGKPenalty(PositionalStrategy):
    def decide(self, data, ids):
        n = len(ids)
        if n != 1:
            raise Exception("Can only decide PrepGKPenalty for 1 robot")

        robot = data.robots[ids[0]]
        ball = data.ball
        field = data.field

        x = 0.05
        y = field.field_width / 2
        theta = atan2(-robot.y + ball.y, -robot.x + ball.x)

        return [x, y, theta]
