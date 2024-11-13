import numpy as np
from math import tan, atan2, pi
from scipy.optimize import linear_sum_assignment
from neonfc_ssl.coach import BaseCoach
from neonfc_ssl.commons.math import distance_between_points
from neonfc_ssl.strategies import Receiver, BallHolder, Test, GoalKeeper, Passer, Libero, RightBack, LeftBack


class Coach(BaseCoach):
    NAME = "TestCoach"

    def _start(self):
        self.keeper = GoalKeeper(self, self._match)
        self.rb = RightBack(self, self._match)
        self.lb = LeftBack(self, self._match)
        self.libero1 = Libero(self, self._match, self.defensive_positions)
        self.libero2 = Libero(self, self._match, self.defensive_positions)
        self.libero3 = Libero(self, self._match, self.defensive_positions)
        self.libero4 = Libero(self, self._match, self.defensive_positions)
        self.ballholder = BallHolder(self, self._match)

    def decide(self):
        # self._active_robots[0].set_strategy(self.rb)
        self._active_robots[0].set_strategy(self.keeper)
        self._active_robots[1].set_strategy(self.libero1)
        self._active_robots[2].set_strategy(self.libero2)
        self._active_robots[3].set_strategy(self.libero3)
        self._active_robots[4].set_strategy(self.libero4)
        self._active_robots[5].set_strategy(self.ballholder)

        n=4
        pos = self._libero_y_positions(n)
        robots = self._active_robots[1:n+1]
        self.cost_matrix(pos, robots)

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
        field = self._match.field
       
        y_goal_min = (field.fieldWidth/2)-field.goalWidth/2
        y_goal_max = (field.fieldWidth/2)+field.goalWidth/2
        x = field.penaltyAreaDepth + 0.2

        y_max = ((y_goal_max-ball.y)/(-ball.x))*(x-ball.x)+ball.y
        y_min = ((y_goal_min-ball.y)/(-ball.x))*(x-ball.x)+ball.y
        if closest < 0.15:
            y = tan(theta)*(x-x_robot)+y_robot
        
        elif ball.x < field.leftPenaltyStretch[0] and ball.y < field.leftPenaltyStretch[1]:
            y = field.leftPenaltyStretch[1] - 0.2
            return y
        
        elif ball.x < field.leftPenaltyStretch[0] and ball.y > (field.fieldWidth - field.leftPenaltyStretch[1]):
            y = (field.fieldWidth - field.leftPenaltyStretch[1]) + 0.2
            return y

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

        ball = self._match.ball
        field = self._match.field
        target = self._ball_proj(x_op, y_op, theta, closest)
        desired_pos = np.zeros((n_robots, 2))
        x = field.penaltyAreaDepth + 0.2
        
        if n_robots == 1:
            desired_pos[0][0] = x
            desired_pos[0][1] = target
            return desired_pos
        
        else:
            diameter = 0.2
            target -= diameter/2
            ang = atan2(ball.vx, ball.vy) if abs(ball.vx) > 0.05 else 0

            for i in range(0, n_robots):
                desired_pos[i][0] = x
                if 1.57 >= ang <= 3.14:
                    desired_pos[i][1] = target + (i * diameter)
                elif -3.14 <= ang <= -1.57:
                    desired_pos[i][1] = target - (i * diameter)
                else:
                    desired_pos[i][1] = target - (i * diameter)
            
            return desired_pos

    def cost_matrix(self, desired_pos, defensive_robots):
        n_robots = len(desired_pos)
        robot_pos = np.zeros((n_robots, 2))
        cost_matrix = np.zeros((n_robots, n_robots))

        i = 0
        for robot in defensive_robots:
            robot_pos[i][0] = robot.x
            robot_pos[i][1] = robot.y
            i += 1

        for i in range(0, n_robots):
            for j in range(0, n_robots):
                cost_matrix[i][j] = (robot_pos[i][0]-desired_pos[j][0])**2+(robot_pos[i][1]-desired_pos[j][1])**2

        lines, columns = linear_sum_assignment(cost_matrix)
        for robot, pos in zip(lines, columns):
            self.defensive_positions[defensive_robots[robot].robot_id] = desired_pos[pos]
