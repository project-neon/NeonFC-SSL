from neonfc_ssl.skills import *
from neonfc_ssl.strategies.base_strategy import BaseStrategy
from math import atan2


class PrepKickoff(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Kickoff', coach, match)

        self.active = MoveToPose(coach, match)

    def _start(self):
        self.active.start(self._robot, target=self.position(self._match.game_state.current_state.color))
        
    def decide(self):
        return self.active.decide()

    def position(self, color):
        field = self._match.field
        if color == self._match.opponent_color:
            x = field.fieldLength/2 - 0.6
        
        else:
            x = field.fieldLength/2 - 0.3

        y = field.fieldWidth/2
        theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)
        
        return [x, y, theta]