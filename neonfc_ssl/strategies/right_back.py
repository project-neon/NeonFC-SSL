from neonfc_ssl.strategies.base_strategy import BaseStrategy
from neonfc_ssl.skills import *
from NeonPathPlanning import Point

from commons.math import distance_between_points
from math import atan2, tan, pi

class RightBack(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('RightBack', coach, match)
        
        self.field = self._match.field
        self.target = None

        self.states = {
            'move_to_right_side': MoveToPose(coach, match),
        }

    def _start(self):
        self.active = self.states['move_to_right_side']
        self.active.start(self._robot, target=self.defense_target)

    def decide(self):
        #print(self.defensive_positions)
        next = self.active.update()
    
        target = self.defense_target()
        self.active = next
        self.active.start(self._robot, target=target)

        return self.active.decide()
    
    def defense_target(self):
        ball = self._match.ball
        field = self._match.field
        y = field.leftPenaltyStretch[1] - 0.2
        
        op_data = self._closest_opponent()
        x_op = op_data[0]
        y_op = op_data[1]
        theta = op_data[2]
        closest = op_data[3]

        target = self._defense_pos(x_op, y_op, theta, closest)
        
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
    
    def _defense_pos(self, x_robot, y_robot, theta, closest):
        ball = self._match.ball
        field = self._match.field
        y = field.leftPenaltyStretch[1] - 0.2

        # x_min = (y-ball.y)*((-ball.x)/(y_goal_min-ball.y))+ball.x
        # x_max = (y-ball.y)*((-ball.x)/(y_goal_max-ball.y))+ball.x
        x_min = 0.15
        x_max = field.leftPenaltyStretch[0]

        if closest < 0.15:
            x = ((y-y_robot)*(1/tan(theta))) + x_robot
        
        elif abs(ball.vx) < 0.05:
            x = ball.x
        
        else:
            x = ((y-ball.y)*(ball.vx/ball.vy)) + ball.x
            theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)

        x = x_max if x > x_max else x
        x = x_min if x < x_min else x
        
        return [x, y, theta]
    