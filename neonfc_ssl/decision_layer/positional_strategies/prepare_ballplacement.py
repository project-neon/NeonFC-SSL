from math import atan2
from positional_strategy import PositionalStrategy


class PrepBallPlacement(PositionalStrategy):
    def decide(self, data, ids):
        n = len(ids)
        if n != 1:
            raise Exception("Can only decide PrepBallPlacement for 1 robot")

        robot = data.robots[ids[0]]
        ball = robot.ball
        field = data.field
        friendly = data.game_state.friendly
        foul_pos = data.game_state.position

        if friendly:
            x = foul_pos[0] - 0.3 
            y = foul_pos[1] 
        
        else:
            if foul_pos[0] < field.field_width/2:
                x = foul_pos[0] - 0.7
                y = foul_pos[1] + 0.7
            
            else:
                x = foul_pos[0] - 0.7
                y = foul_pos[1] - 0.7

        theta = atan2(-robot.y + ball.y, -robot.x + ball.x)
        
        return [x, y, theta]
