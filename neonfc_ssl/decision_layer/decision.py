import logging
from abc import ABC, abstractmethod
from scipy.optimize import linear_sum_assignment
import numpy as np
from neonfc_ssl.core import Layer
from .decision_data import DecisionData, RobotRubric
from .coaches import COACHES

from typing import TYPE_CHECKING, Union, Optional
if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData, TrackedRobot
    from neonfc_ssl.decision_layer.special_strategies import BaseStrategy


Position = tuple[float, float]
Pose = tuple[float, float, float]


class Decision(Layer):
    def __init__(self, config, log_q, event_pipe):
        super().__init__("DecisionLayer", config, log_q, event_pipe)
        self.events = {}
        self.__strategies: list[Optional['BaseStrategy']] = []

    def _start(self):
        self.log(logging.INFO, "Starting coach module starting ...")

        self.__strategies = [None for _ in range(16)]

        self.__coach = COACHES['TestCoach'](self)

        self.log(logging.INFO, "Coach module started!")

    def decide(self, data: 'MatchData'):
        return self.__coach(data)

    @staticmethod
    def _check_halt(data: 'MatchData'):
        if data.game_state == "Halt":
            return True
        return False

    def set_strategy(self, robot: 'TrackedRobot', strategy: 'BaseStrategy'):
        if robot.id > len(self.__strategies):
            self.log(logging.ERROR, "Trying to set strategy for unknown id {}".format(id))
            return
        if self.__strategies[robot.id] == strategy:
            return

        self.__strategies[robot.id] = strategy
        self.__strategies[robot.id].start(robot.id)

    def _step(self, data: 'MatchData') -> 'DecisionData':
        if self._check_halt(data):
            return DecisionData([RobotRubric.still(r.id) for r in data.robots.active], data)

        self.__commands = []
        self.__hungarian_robots = []

        self.decide(data)

        for robot in data.robots.active:
            if robot in self.__hungarian_robots:
                continue

            if strat := self.__strategies[robot.id]:
                try:
                    self.__commands.append(strat.decide(data))
                except KeyboardInterrupt as e:
                    raise e
                except Exception as e:
                    raise e
                    self.log(logging.ERROR, e)

        return DecisionData(self.__commands, data)

    @property
    def has_possession(self):
        # FIXME
        return self._match.possession.get_possession() == self._match.team_color

    def calculate_hungarian(self, targets: list[Union[Position, Pose]], robots: list['TrackedRobot']):
        try:
            rs, ps = self.__cost_matrix(targets, robots)
        except Exception as e:
            self.log(logging.ERROR, e)
            return

        for robot, pos in zip(rs, ps):
            if len(pos) == 2:
                pos.append(robot.theta)

            self.__hungarian_robots.append(robot.id)

            self.__commands.append(RobotRubric(
                id=robot.id,
                halt=False,
                target_pose=pos
            ))

    @staticmethod
    def __cost_matrix(desired_pos: list[Union[Position, Pose]], defensive_robots: list['TrackedRobot']):
        if len(defensive_robots) != len(desired_pos):
            raise Exception("Number of defensive robots must equal number of desired poses")

        n_robots = len(desired_pos)

        robot_pos = np.zeros((n_robots, 2))
        cost_matrix = np.zeros((n_robots, n_robots))

        for idx, robot in enumerate(defensive_robots):
            robot_pos[idx][0] = robot.x
            robot_pos[idx][1] = robot.y

        try:
            for i in range(n_robots):
                for j in range(n_robots):
                    cost_matrix[i][j] = (robot_pos[i][0]-desired_pos[j][0])**2 + (robot_pos[i][1]-desired_pos[j][1])**2
        except IndexError as e:
            raise Exception(e)

        return linear_sum_assignment(cost_matrix)
