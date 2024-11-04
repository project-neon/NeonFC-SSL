import numpy as np
from math import tan, atan2, pi
from scipy.optimize import linear_sum_assignment
from neonfc_ssl.coach import BaseCoach
from neonfc_ssl.commons.math import distance_between_points
from neonfc_ssl.strategies import Receiver, BallHolder, GoalKeeper, Libero


class Coach(BaseCoach):
    NAME = "TestCoach"

    def _start(self):
        self.test = GoalKeeper(self, self._match)
        self.test2 = Libero(self, self._match, self.defensive_positions)
        self.test3 = Libero(self, self._match, self.defensive_positions)
        self.test4 = Libero(self, self._match, self.defensive_positions)

    def decide(self):
        self._active_robots[0].set_strategy(self.test)
        self._active_robots[1].set_strategy(self.test2)
        self._active_robots[2].set_strategy(self.test3)
        self._libero_y_positions(3)

    
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

    def _ball_proj(self, x_robot, y_robot, theta, closest):
        ball = self._match.ball
        y_goal_min = 2.5 
        y_goal_max = 3.5 
        x = 1.2

        y_max = ((y_goal_max-ball.y)/(-ball.x))*(x-ball.x)+ball.y
        y_min = ((y_goal_min-ball.y)/(-ball.x))*(x-ball.x)+ball.y

        if closest < 0.15:
            y = tan(theta)*(x-x_robot)+y_robot
        
        elif abs(ball.vx) < 0.05:
            y = ball.y
        
        else:
            y = (ball.vy/ball.vx)*(x-ball.x)+ball.y

        y = y_max if y > y_max else y
        y = y_min if y < y_min else y
        
        return y

    def _libero_y_positions(self, n_robots):
        data = self._closest_opponent()
        x_op = data[0]
        y_op = data[1]
        theta = data[2]
        closest = data[3]

        target = self._ball_proj(x_op, y_op, theta, closest)
        
        if n_robots == 1:
            return target
        
        else:
            x = 1.2
            ball = self._match.ball
            desired_pos = np.zeros((n_robots, 2))
            robot_pos = np.zeros((n_robots, 2))
            cost_matrix = np.zeros((n_robots, n_robots))

            diameter = 0.2
            target -= diameter
            ang = atan2(ball.vx, ball.vy) if ball.vx != 0 else 0

            for i in range(0, n_robots):
                desired_pos[i][0] = x
                if 1.57 >= ang <= 3.14:
                    desired_pos[i][1] = target + (i * diameter)
                elif -3.14 <= ang <= -1.57:
                    desired_pos[i][1] = target - (i * diameter)

            i = 0
            for robot in self._match.active_robots:
                robot_pos[i][0] = robot.x
                robot_pos[i][1] = robot.y
                i += 1

            i = 0
            j = 0
            for i in range(0, n_robots):
                for j in range(0, n_robots):
                    cost_matrix[i][j] = (robot_pos[i][0]-desired_pos[j][0])**2+(robot_pos[i][1]-desired_pos[j][1])**2

            lines, columns = linear_sum_assignment(cost_matrix)
            # print(f'target: {desired_pos}')
            # print(f'actual: {robot_pos}')
            # print(cost_matrix)
            for robot, pos in zip(lines, columns):
                y = desired_pos[pos][1]
                self.defensive_positions[f'libero_{robot}'] = y
