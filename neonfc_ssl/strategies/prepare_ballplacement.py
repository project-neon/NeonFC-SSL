from neonfc_ssl.skills import *
from neonfc_ssl.strategies.base_strategy import BaseStrategy
from math import atan2, cos, sin


class PrepBallPlacement(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('BallPlacement', coach, match)

        self.states = {
            'wait': Wait(coach, match),
            'move_to_pose': MoveToPose(coach, match)
        }

        self.states['wait'].add_transition(self.states['move_to_pose'], self.move_to_pose_transition)

    def _start(self):
        self.active = self.states['wait']
        self.active.start(self._robot)
        
    def decide(self):
        next = self.active.update()
        target = self.position()
        self.active = next
        self.active.start(self._robot, target=target)

        com = self.active.decide()
        com.ignore_ball = False
        return com

    def position(self):
        field = self._match.field

        ang = atan2(-self._match.ball.y + field.fieldWidth/2, -self._match.ball.x)

        x = self._match.ball.x + cos(ang)*0.65
        y = self._match.ball.y + sin(ang)*0.65

        theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)
        
        return [x, y, theta]
    
    def move_to_pose_transition(self):
        return True