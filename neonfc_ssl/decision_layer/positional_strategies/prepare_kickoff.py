from math import atan2
from .positional_strategy import PositionalStrategy


class PrepKickoff(PositionalStrategy):
    def decide(self, data, ids):
        n = len(ids)
        if n != 1:
            raise Exception("Can only decide PrepKickoff for 1 robot")

        robot = data.robots[ids[0]]
        ball = robot.ball
        field = data.field
        friendly = data.game_state.friendly

        if friendly:
            x = field.field_length/2 - 0.3
        
        else:
            x = field.field_length/2 - 0.6

        y = field.field_width/2
        theta = atan2(-robot.y + ball.y, -robot.x + ball.x)
        
        return [x, y, theta]
