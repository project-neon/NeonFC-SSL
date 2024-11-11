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
        target_theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)
        return *self.expected_position(), target_theta

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

    def expected_position(self):
        return self._defense_pos(*self._closest_opponent())

    def _defense_pos(self, x_robot, y_robot, theta, closest):
        y = self.y_position()
        x = self.x_position(x_robot, y_robot, theta, closest)

        return x, y

    def x_position(self, x_robot, y_robot, theta, closest):
        ball = self._match.ball
        field = self._match.field
        y = self.y_position()
        x_min = 0.15
        x_max = field.leftPenaltyStretch[0]

        if closest < 0.15:
            x = ((y-y_robot)*(1/tan(theta))) + x_robot

        elif abs(ball.vx) < 0.05:
            x = ball.x

        else:
            x = ((y-ball.y)*(ball.vx/ball.vy)) + ball.x

        return max(x_min, min(x_max, x))

    def y_position(self):
        field = self._match.field
        return field.leftPenaltyStretch[1] - 0.2

    