from neonfc_ssl.skills import *
from neonfc_ssl.strategies.base_strategy import BaseStrategy
from math import atan2


class Kickoff(BaseStrategy):
    def __init__(self, name, coach, match):
        super().__init__('Kickoff', coach, match)
        self.name = name
        self._match = match
        self._coach = coach
        self._robot = None

        self.states = {
            'wait': Wait(coach, match),
            'move_to_pose': MoveToPose(coach, match)
        }

        self.states['wait'].add_transition(self.states['move_to_pose'])

    def _start(self):
        self.active = self.states['Wait']
        self.active.start(self._robot)
        
    def decide(self):
        next = self.active.update()
        color = self._match.game_state.current_state.color

        target = self.position(color)
        self.active = next
        self.active.start(self._robot, target=target)

        return self.active.decide()

    def position(self, color):
        field = self._match.field
        if color == self._match.opponent_color:
            x =  field.fieldLength/2 - 0.5
        
        else:
            x = field.fieldLength - 0.3

        y =  field.fieldWidth/2
        theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)
        
        return [x, y, theta]
    
    def move_to_pose_transition(self):
        return True