from neonfc_ssl.skills import *
from neonfc_ssl.strategies.base_strategy import BaseStrategy
from neonfc_ssl.commons.math import distance_between_points
from math import atan2


class PrepKickoff(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Kickoff', coach, match)

        self.skills = {
            'position': MoveToPose(coach, match),
            'pass': SimplePass(coach, match)
        }

        self.skills['position'].add_transition(self.skills['pass'], self.skills['position'].complete)

        self.active = self.skills['position']

    def _start(self):
        self.active.start(self._robot, target=self.position(self._match.game_state.current_state.color))
        
    def decide(self):
        next_state = self.active.update()
        if next_state != self.active:
            self.active = next_state
            nearest = min(self._match.active_robots,
                          key=lambda x: distance_between_points(self._robot, x) if x != self._robot else float('inf'),
                          default=[0, 0])
            self.active.start(self._robot, target=nearest)

        com = self.active.decide()
        com.ignore_ball = False
        return com

    def position(self, color):
        field = self._match.field

        if color == self._match.opponent_color:
            x = field.fieldLength/2 - 0.6
            y = field.fieldWidth / 2
        else:
            x = field.fieldLength/2 + 0.2
            y = field.fieldWidth / 2 + 0.2

        theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)
        
        return [x, y, theta]