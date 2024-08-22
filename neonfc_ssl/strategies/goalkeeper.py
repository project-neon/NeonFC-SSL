from neonfc_ssl.strategies.base_strategy import BaseStrategy
from neonfc_ssl.skills import *
from NeonPathPlanning import Point

from commons.math import point_in_rect
from math import pi

class GoalKeeper(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Goalkeeper', coach, match)
        
        self.field = self._match.field
        self.target = None

        self.states = {
            'pass': SimplePass(coach, match),
            'go_to_ball': GoToBall(coach, match),
            'wait': Wait(coach, match),
            'move_to_pose': MoveToPose(coach, match)
        }

        self.states["wait"].add_transition(self.states["move_to_pose"], self.move_to_pose_transition)
        self.states["move_to_pose"].add_transition(self.states["go_to_ball"], self.go_to_ball_transition)
        self.states["move_to_pose"].add_transition(self.states["wait"], self.wait_transition)
        self.states["go_to_ball"].add_transition(self.states["pass"], self.pass_transisition)
        self.states["pass"].add_transition(self.states["move_to_pose"], self.move_to_pose_transition)


    def _start(self):
        self.active = self.states['wait']
        self.active.start(self._robot)

    def decide(self):
        next = self.active.update()
    
        if next.name != "MoveToPose":
            self.active = next
            
            if self.active.name == "Pass":
                _passing_to = Point(2, 2)
                self.active.start(self._robot, target=_passing_to)
            
            else:
                self.active.start(self._robot)
        
        else:
            target = self.defense_target()
            self.active = next
            self.active.start(self._robot, target=target)

        return self.active.decide()
    
    def defense_target(self):
        return [0.2, self._match.ball.y, 0]

    def wait_transition(self):
        if self._match.ball.x > self.field.halfwayLine[0]:
            return True
        return False


    def move_to_pose_transition(self):
        is_in_rect = point_in_rect([self._match.ball.x, self._match.ball.y],
                                      [self.field.leftFirstPost[0], self.field.leftFirstPost[1],
                                       self.field.goalWidth, 2*self.field.fieldLength])
        
        if not is_in_rect and self._match.ball.x <= self.field.halfwayLine[0]:
            return True
        return False


    def go_to_ball_transition(self):
        # is_in_rect = point_in_rect([self._match.ball.x, self._match.ball.y],
        #                               [self.field.leftFirstPost[0], self.field.leftFirstPost[1],
        #                                self.field.goalWidth, 0])
        
        if (self._match.ball.x < 1) and (self._match.ball.y > 2) and (self._match.ball.y < 4):
            return True        
        return False


    def pass_transisition(self):
        is_in_rect = point_in_rect([self._match.ball.x, self._match.ball.y],
                                      [self._robot.x-0.15, self._robot.y-0.15, 0.3, 0.3])
        
        if is_in_rect:
            return True
        return False