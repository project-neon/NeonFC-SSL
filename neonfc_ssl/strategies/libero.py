from neonfc_ssl.strategies.base_strategy import BaseStrategy
from neonfc_ssl.skills import *
from NeonPathPlanning import Point

from neonfc_ssl.commons.math import point_in_rect, distance_between_points
from math import atan2, tan, pi

class Libero(BaseStrategy):
    def __init__(self, coach, match, defensive_positions):
        super().__init__('Libero', coach, match)
        
        self.defensive_positions = defensive_positions
        self.field = self._match.field
        self.target = None

        self.states = {
            'go_to_ball': GoToBall(coach, match),
            'move_to_pose': MoveToPose(coach, match)
        }

        self.states["move_to_pose"].add_transition(self.states["go_to_ball"], self.go_to_ball_transition)
        self.states["go_to_ball"].add_transition(self.states["move_to_pose"], self.move_to_pose_transition)

    def _start(self):
        self.active = self.states['move_to_pose']
        self.active.start(self._robot, target=self.defense_target)

    def decide(self):
        #print(self.defensive_positions)
        next = self.active.update()
        
        if next.name != "MoveToPose":
            self.active = next    
            self.active.start(self._robot)
        
        else:
            target = self.defense_target()
            self.active = next
            self.active.start(self._robot, target=target)

        return self.active.decide()
    
    def defense_target(self):
        ball = self._match.ball
        x = 1.2
        
        if ball.vx == 0:
            return [self._robot.x, self._robot.y, self._robot.theta]
        
        elif ball.x > self.field.halfwayLine[0]:
            return [x, self.field.fieldWidth/2, 0]
        
        op_data = self._closest_opponent()
        x_op = op_data[0]
        y_op = op_data[1]
        theta = op_data[2]
        closest = op_data[3]

        if ball.y > 4 and ball.x < 1:
            target = self._defense_up(x_op, y_op, theta, closest)
        
        elif ball.y < 2 and ball.x < 1:
                       target = self._defense_down(x_op, y_op, theta, closest)
        
        else:
            target = self._defense_front(x_op, y_op, theta, closest)

        return [target[0], target[1], target[2]]

    def _closest_opponent(self):
        ball = self._match.ball

        closest = 100000
        for robot in self._match.opposites:
            dist = distance_between_points([ball.x, ball.y], [robot.x, robot.y])
            if dist < closest:
                closest = dist
                theta = robot.theta - pi
                x_robot = robot.x
                y_robot = robot.y
                data = [x_robot, y_robot, theta, closest]
        
        return data

    def _defense_front(self, x_robot, y_robot, theta, closest):
        x = 1.2
        y = self.defensive_positions[f'libero_{self._robot.robot_id-1}']
        # print(f"robot_{self._robot.robot_id}: desired_y = {y}")
        theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)

        return [x, y, theta]
    
    def _defense_up(self, x_robot, y_robot, theta, closest):
        ball = self._match.ball
        y_goal_min = 2.5 
        y_goal_max = 3.5 
        y = 4.2

        x_min = (y-ball.y)*((-ball.x)/(y_goal_max-ball.y))+ball.x 
        x_max = (y-ball.y)*((-ball.x)/(y_goal_min-ball.y))+ball.x

        if closest < 0.15:
            x = ((y-y_robot)*(1/tan(theta))) + x_robot
        
        else:
            x = ((y-ball.y)*(ball.vx/ball.vy)) + ball.x
            theta = ball.vx/ball.vy

        x = x_max if x > x_max else x
        x = x_min if x < x_min else x

        return [x, y, theta]
    
    def _defense_down(self, x_robot, y_robot, theta, closest):
        ball = self._match.ball
        y_goal_min = 2.5 
        y_goal_max = 3.5 
        y = 1.8

        x_min = (y-ball.y)*((-ball.x)/(y_goal_min-ball.y))+ball.x
        x_max = (y-ball.y)*((-ball.x)/(y_goal_max-ball.y))+ball.x

        if closest < 0.15:
            x = ((y-y_robot)*(1/tan(theta))) + x_robot
        
        else:
            x = ((y-ball.y)*(ball.vx/ball.vy)) + ball.x
            theta = ball.vx/ball.vy

        x = x_max if x > x_max else x
        x = x_min if x < x_min else x

        return [x, y, theta]
    
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
