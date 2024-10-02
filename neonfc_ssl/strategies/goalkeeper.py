from neonfc_ssl.strategies.base_strategy import BaseStrategy
from neonfc_ssl.skills import *
from NeonPathPlanning import Point

from commons.math import point_in_rect, distance_between_points
from math import tan, pi

class GoalKeeper(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Goalkeeper', coach, match)
        
        self.field = self._match.field
        self.target = None

        self.states = {
            'pass': SimplePass(coach, match),
            'go_to_ball': GoToBall(coach, match),
            'move_to_pose': MoveToPose(coach, match)
        }

        def not_func(f):
            def wrapped():
                return not f()

            return wrapped

        self.states["move_to_pose"].add_transition(self.states["go_to_ball"], self.go_to_ball_transition)
        self.states["go_to_ball"].add_transition(self.states["pass"], self.pass_transisition)
        self.states["go_to_ball"].add_transition(self.states["move_to_pose"], not_func(self.go_to_ball_transition))
        self.states["pass"].add_transition(self.states["move_to_pose"], self.move_to_pose_transition)


    def _start(self):
        self.active = self.states['move_to_pose']
        self.active.start(self._robot, target=self.defense_target)

    def decide(self):
        next = self.active.update()
        
        if next.name != "MoveToPose":
            self.active = next
            print(self.active.name)
            
            if self.active.name == "Pass":
                _passing_to = Point(5, 4)
                self.active.start(self._robot, target=_passing_to)
            
            else:
                self.active.start(self._robot)
        
        else:
            print(self.active.name)
            target = self.defense_target()
            self.active = next
            self.active.start(self._robot, target=target)

        return self.active.decide()
    
    def defense_target(self):
        ball = self._match.ball
        y_goal_min = 2.5 + 0.15
        y_goal_max = 3.5 - 0.15
        x = 0.2
        
        if ball.vx == 0:
            return [self._robot.x, self._robot.y, self._robot.theta]
        
        elif ball.x > self.field.halfwayLine[0]:
            return [x, self.field.fieldWidth/2, 0]

        y_max = ((y_goal_max-ball.y)/(-ball.x))*(x-ball.x)+ball.y
        y_min = ((y_goal_min-ball.y)/(-ball.x))*(x-ball.x)+ball.y

        closest = 100000
        for robot in self._match.opposites:
            dist = distance_between_points([ball.x, ball.y], [robot.x, robot.y])
            if dist < closest:
                closest = dist
                theta = robot.theta - pi
                x_robot = robot.x
                y_robot = robot.y
            
                
        if closest < 0.15:
            y = tan(theta)*(x-x_robot)+y_robot
        
        else:
            y = (ball.vy/ball.vx)*(x-ball.x)+ball.y
            theta = ball.vy/ball.vx
        
        if ball.y > self.field.fieldWidth/2:
            y += 0.1
        
        else:
            y -= 0.1

        y = max(min(y, y_max, y_goal_max), y_min, y_goal_min)

        return [x, y, theta]
    
    
    def ball_in_area(self):
        if (self._match.ball.x < 1) and (self._match.ball.y > 2) and (self._match.ball.y < 4):
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
        if (self._match.ball.x < 1) and (self._match.ball.y > 2) and (self._match.ball.y < 4):
            return True        
        return False


    def pass_transisition(self):
        is_in_rect = point_in_rect([self._match.ball.x, self._match.ball.y],
                                      [self._robot.x-0.15, self._robot.y-0.15, 0.3, 0.3])
        
        if is_in_rect and self.ball_in_area():
            return True        
        return False