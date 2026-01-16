import logging
from scipy.optimize import linear_sum_assignment
import numpy as np
from neonfc_ssl.core import Layer
from neonfc_ssl.core.event import EventType, Event, event_callback
from .decision_data import DecisionData, RobotRubric
from .coaches import COACHES
from neonfc_ssl.tracking_layer.tracking_data import States

from typing import TYPE_CHECKING, Union, Optional
if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData, TrackedRobot
    from .special_strategies.special_strategy import SpecialStrategy
    from .positional_strategies.positional_strategy import PositionalStrategy


Position = tuple[float, float]
Pose = tuple[float, float, float]
POSITION_INDEX = 0
STRATEGY_INDEX = 1


class Decision(Layer):
    def __init__(self, config, log_q):
        super().__init__("DecisionLayer", config, log_q)
        self.events = {}
        self.__strategies: list[Optional['SpecialStrategy']] = []
        self.__force_halt = False

        self.logger = logging.getLogger('DecisionLayer')

    @event_callback(event_type=EventType.MASTER_STATE)
    def master_state_event(self, event: Event):
        state = event.event_data['new_state']
        if state == "play":
            self.__force_halt = False

        if state == "halt":
            self.__force_halt = True

    def _start(self):
        self.logger.info("Starting coach module starting ...")

        self.__strategies = [None for _ in range(16)]

        self.__coach = COACHES[self.config['coach']](self)

        self.logger.info("Coach module started!")

    def decide(self, data: 'MatchData'):
        return self.__coach(data)

    def get_strategy(self, robot_id):
        return self.__strategies[robot_id]

    def _check_halt(self, data: 'MatchData'):
        if self.__force_halt:
            return True
        if data.game_state.state in (States.HALT, States.TIMEOUT):
            return True
        return False

    def set_strategy(self, robot: 'TrackedRobot', strategy: 'SpecialStrategy'):
        if robot.id > len(self.__strategies):
            self.logger.error("Trying to set strategy for unknown id {}".format(id))
            return
        if self.__strategies[robot.id] == strategy:
            return

        self.__strategies[robot.id] = strategy
        self.__strategies[robot.id].start(robot.id)

    def disable_robot(self, robot: "TrackedRobot"):
        self.__strategies[robot.id] = None

    def _step(self, data: 'MatchData') -> 'DecisionData':
        if self._check_halt(data):
            return DecisionData([RobotRubric.still(r.id) for r in data.robots.active], data)

        self.__commands = []
        self.__hungarian_robots = []

        self.decide(data)

        for robot in data.robots.active:
            if robot.id in self.__hungarian_robots:
                continue

            if strat := self.__strategies[robot.id]:
                try:
                    cmd = strat.decide(data)
                    if cmd is None:
                        raise ValueError(f"robot {robot.id} strategy returned None", strat)
                    self.__commands.append(cmd)
                except KeyboardInterrupt as e:
                    raise e
                except Exception as e:
                    self.logger.error(e)
                    raise e

        return DecisionData(self.__commands, data)

    def calculate_hungarian(self, targets: list[tuple[Union[Position, Pose], "PositionalStrategy"]],
                            robots: list['TrackedRobot']):
        try:
            rs, ps = self.__cost_matrix(targets, robots)
        except Exception as e:
            self.logger.error(e)
            return

        for robot, pos in zip(rs, ps):
            if len(targets[pos][POSITION_INDEX]) == 2:
                target_pose = (*targets[pos][POSITION_INDEX], robots[robot].theta)
            else:
                target_pose = targets[pos][POSITION_INDEX]

            self.__strategies[robots[robot].id] = targets[pos][STRATEGY_INDEX]()
            self.__hungarian_robots.append(robots[robot].id)

            self.__commands.append(RobotRubric(
                id=robots[robot].id,
                halt=False,
                target_pose=target_pose
            ))

    @staticmethod
    def __cost_matrix(desired_pos: list[tuple[Union[Position, Pose], "PositionalStrategy"]],
                      defensive_robots: list['TrackedRobot']):
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
                    # TODO: this is using the a straight line distance to the target as the cost, but it's not always
                    #       the case (eg. A robot won't pass thru the area, so if the straight line goes thru it the
                    #       real cost is higher)
                    cost_matrix[i][j] = (
                        (robot_pos[i][0]-desired_pos[j][POSITION_INDEX][0])**2 +
                        (robot_pos[i][1]-desired_pos[j][POSITION_INDEX][1])**2
                    )
        except IndexError as e:
            raise Exception(e)

        return linear_sum_assignment(cost_matrix)
