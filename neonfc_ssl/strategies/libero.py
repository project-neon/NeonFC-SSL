from neonfc_ssl.strategies.base_strategy import BaseStrategy
from neonfc_ssl.skills import *
from NeonPathPlanning import Point

from neonfc_ssl.commons.math import point_in_rect, distance_between_points, reduce_ang
from math import tan, pi, atan2

class Libero(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Libero', coach, match)
        
        self.field = self._match.field
        self.target = None

        self.states = {
            'move_to_pose': MoveToPose(coach, match)
        }

    def _start(self):
        self.active = self.states['move_to_pose']
        self.active.start(self._robot, target=self.defense_target)

    def decide(self):
        next = self.active.update()
        
        if next.name != "MoveToPose":
            self.active = next    
            self.active.start(self._robot)
        
        else:
            target = self.defense_target()
            self.active = next
            self.active.start(self._robot, target=target)

        return self.active.decide()

    # calcula a posição de defesa para o libero
    def defense_target(self):
        ball = self._match.ball
        x = 0.55

        if ball.vx > 0.05:
            return [x, ball.y, 0]
        
        elif ball.x > self.field.halfwayLine[0]:
            return [x, self.field.fieldWidth/2, 0]
        
        op_data = self._closest_opponent()
        x_op = op_data[0]
        y_op = op_data[1]
        theta = op_data[2]
        closest = op_data[3]

        # bola ao lado da área (lateral direita)
        if ball.y < (self.field.fieldWidth-self.field.penaltyAreaWidth)/2 and ball.x < self.field.penaltyAreaDepth:
            target = self._defense_down(x_op, y_op, theta, closest)

        # bola ao lado da área (lateral esquerda)
        elif ball.y > ((self.field.fieldWidth-self.field.penaltyAreaWidth)/2) + self.field.penaltyAreaWidth and ball.x < self.field.penaltyAreaDepth:
            target = self._defense_up(x_op, y_op, theta, closest)

        # bola na frente da área
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
        ball = self._match.ball
        # y_goal_min = 2.5
        # y_goal_max = 3.5
        y_goal_min = 0.2 + 0.1
        y_goal_max = 1.34 - 0.1
        x = 0.55

        y_max = ((y_goal_max-ball.y)/(-ball.x))*(x-ball.x)+ball.y
        y_min = ((y_goal_min-ball.y)/(-ball.x))*(x-ball.x)+ball.y

        # robo adversario perto da bola
        if closest < 0.15:
            y = tan(theta)*(x-x_robot)+y_robot

        # bola quase parada
        elif abs(ball.vx) < 0.05:
            y = ball.y
            theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)
            return [x, y, theta]

        #proj da bola
        else:
            y = (ball.vy/ball.vx)*(x-ball.x)+ball.y
            theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)

        y = y_max if y > y_max else y
        y = y_min if y < y_min else y

        theta = reduce_ang(theta)
        return [x, y, theta]
    
    def _defense_up(self, x_robot, y_robot, theta, closest):
        ball = self._match.ball
        y_goal_min = 0.2 + 0.1
        y_goal_max = 1.34 - 0.1
        y = 1.44

        x_min = (y-ball.y)*((-ball.x)/(y_goal_max-ball.y))+ball.x 
        x_max = (y-ball.y)*((-ball.x)/(y_goal_min-ball.y))+ball.x

        # advesario perto da bola
        if closest < 0.15:
            x = ((y-y_robot)*(1/tan(theta))) + x_robot

        # bola quase parada
        elif abs(ball.vx) < 0.05:
            x = ball.x
            theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)
            return [x, y, theta]

        # proj da bola
        else:
            x = ((y-ball.y)*(ball.vx/ball.vy)) + ball.x
            theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)

        x = x_max if x > x_max else x
        x = x_min if x < x_min else x

        theta = reduce_ang(theta)
        return [x, y, theta]
    
    def _defense_down(self, x_robot, y_robot, theta, closest):
        ball = self._match.ball
        y_goal_min = 0.2 + 0.1
        y_goal_max = 1.34 - 0.1
        y = 0.1

        x_min = (y-ball.y)*((-ball.x)/(y_goal_min-ball.y))+ball.x
        x_max = (y-ball.y)*((-ball.x)/(y_goal_max-ball.y))+ball.x

        # adversario proximo da bola
        if closest < 0.15:
            x = ((y-y_robot)*(1/tan(theta))) + x_robot

        # bola quase parada
        elif abs(ball.vx) < 0.05:
            x = ball.x
            theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)
            return [x, y, theta]

        # proj da bola
        else:
            x = ((y-ball.y)*(ball.vx/ball.vy)) + ball.x
            theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)

        x = x_max if x > x_max else x
        x = x_min if x < x_min else x

        theta = reduce_ang(theta)
        return [x, y, theta]