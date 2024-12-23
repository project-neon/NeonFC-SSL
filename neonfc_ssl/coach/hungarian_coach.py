from neonfc_ssl.coach import BaseCoach
from neonfc_ssl.strategies import Still, FollowPose
from scipy.optimize import linear_sum_assignment
import numpy as np
from abc import ABC


class Coach(BaseCoach, ABC):
    def __init__(self, game):
        super().__init__(game)

        self.hungarian_targets = {}
        self.position_strategies = {}

    def start(self):
        self.logger.info("Starting coach module starting ...")

        # Last Layer Classes
        self._match = self._game.match
        self._robots = self._match.robots

        for r in self._robots:
            r.set_strategy(Still(self, self._match))

        self.position_strategies = {
            r_id: FollowPose(self, self._match) for r_id in range(6)
        }

        self.hungarian_targets = {
            r_id: FollowPose.Pose(0, 0, 0) for r_id in range(6)
        }

        self._start()

        self.logger.info("Coach module started!")

    def _calculate_hungarian(self, robots, targets):
        self.__cost_matrix(targets, robots)
        for robot in robots:
            robot.set_strategy(self.position_strategies[robot.robot_id])

    def __cost_matrix(self, desired_pos, defensive_robots):
        if len(defensive_robots) != len(desired_pos):
            raise ValueError("Number of defensive robots must equal number of desired poses")

        n_robots = len(desired_pos)
        robot_pos = np.zeros((n_robots, 2))
        cost_matrix = np.zeros((n_robots, n_robots))

        for robot in defensive_robots:
            robot_pos[robot.robot_id][0] = robot.x
            robot_pos[robot.robot_id][1] = robot.y

        for i in range(n_robots):
            for j in range(n_robots):
                cost_matrix[i][j] = (robot_pos[i][0] - desired_pos[j][0]) ** 2 + (
                            robot_pos[i][1] - desired_pos[j][1]) ** 2

        lines, columns = linear_sum_assignment(cost_matrix)
        for robot, pos in zip(lines, columns):
            self.hungarian_targets[defensive_robots[robot].robot_id].update(desired_pos[pos])
