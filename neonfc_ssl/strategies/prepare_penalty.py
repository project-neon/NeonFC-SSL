from neonfc_ssl.skills import *
from neonfc_ssl.strategies.base_strategy import BaseStrategy
from math import atan2
import numpy as np
from scipy.optimize import linear_sum_assignment


class PrepPenalty(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Penalty', coach, match)

        self.states = {
            'wait': Wait(coach, match),
            'move_to_pose': MoveToPose(coach, match)
        }

        self.states['wait'].add_transition(self.states['move_to_pose'], self.move_to_pose_transition)

        self.defensive_positions = {}

    def _start(self):
        self.active = self.states['wait']
        self.active.start(self._robot)
        
    def decide(self):
        next = self.active.update()
        target = self.position()
        self.active = next
        self.active.start(self._robot, target=target)

        return self.active.decide()

    def position(self):
        field = self._match.field

        x = field.fieldLength/2 + 0.2
        penalty_pos = []

        non_keepers = [r for r in self._match.active_robots if r.strategy.name != "Goalkeeper"]

        # if color == self._match.opponent_color:
        i = 0
        for j in range(1, len(non_keepers)+1):
            penalty_pos.append((field.fieldLength/2 + 0.5, (j * (5/6)) + (0.2 * (j - 1)) + 0.1))

        theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)

        self.cost_matrix(penalty_pos, non_keepers)
        p = self.defensive_positions[self._robot.robot_id]
        
        return *p, theta

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
    

    def move_to_pose_transition(self):
        return True