import math
from .base_coach import Coach
from neonfc_ssl.commons.math import distance_between_points
from ..special_strategies import BallHolder, GoalKeeper
from ..positional_strategies import Libero, LeftBack, RightBack, PrepPenalty, PrepBallPlacement, PrepKickoff, PrepGKPenalty, PrepBHPenalty
from neonfc_ssl.tracking_layer.tracking_data import States
from scipy.optimize import linear_sum_assignment
import numpy as np

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import TrackedRobot


USE_FOULS = True


class SimpleCoach(Coach):
    def _start(self):
        # Create strategies' objects

        # Especial cases
        self._strategy_gk = GoalKeeper(self.decision.logger)
        self._strategy_bh = BallHolder(self.decision.logger)
        self._gk_id = 0

        # ------ n=6 ------ #
        # 1 fixed keeper
        #   when ball is inside area the keeper becomes the ball holder
        #
        # When ball-less
        # 3 defense robots (Libero/LeftBack/RightBack)
        # 1 ball holder
        # 1 fixed attacker
        #
        # When in possession
        # 2 defense robots
        # 1 ball holder
        # 2 attackers

        # self._libero_strategies = {
        #     r_id: Libero(self, self._match, self.defensive_positions) for r_id in range(6)
        # }

        # self._left_back_strategy = LeftBack(self, self._match)
        # self._right_back_strategy = RightBack(self, self._match)

        # Default attack strategies
        # self._secondary_attack_strategies: dict[int, 'BaseStrategy'] = {
        #     robot.robot_id: Receiver(self, self._match) for robot in self._match.robots if robot.robot_id != self._gk_id
        # }
        # self._secondary_attack_strategies[self._gk_id] = self._strategy_gk

    def decide(self):
        if self.has_possession():
            self._defending()
        else:
            self._defending()

        if USE_FOULS and self.data.game_state.state != States.RUN:
            self._fouls()

    def _fouls(self):
        if self.data.game_state.state == States.PREPARE_KICKOFF:
            self.replace_strategy(BallHolder, PrepKickoff)
            return

        if self.data.game_state.state == States.PREPARE_PENALTY:
            if self.data.game_state.friendly:
                self.replace_strategy(BallHolder, PrepBHPenalty)
            else:
                self.replace_strategy(GoalKeeper, PrepGKPenalty)
                self.replace_strategy((GoalKeeper, PrepGKPenalty), PrepPenalty, avoid_list=True)
            return

        if self.data.game_state.state == States.PENALTY:
            if not self.data.game_state.friendly:
                self.replace_strategy((GoalKeeper, PrepGKPenalty), PrepPenalty, avoid_list=True)
            return

        if self.data.game_state.state in (States.BALL_PLACEMENT, States.FREE_KICK, States.STOP):
            self.replace_strategy(BallHolder, PrepBallPlacement)
            return


    def replace_strategy(self, old_strategies, new_strategy, avoid_list=False):
        robots = list(filter(
            lambda r: avoid_list != isinstance(self.get_strategy(r.id), old_strategies), # XOR on avoid_list
            self.data.robots.actives
        ))
        self.decision.calculate_hungarian(
            targets=new_strategy.decide(self.data, [r.id for r in robots]),
            robots=robots
        )

    def _defending(self):
        # when in possession, check the ball carrier (smaller time to ball), then it becomes ball carrier
        new_carrier = self._closest_non_keeper()

        self.decision.set_strategy(self.data.robots[self._gk_id], self._strategy_gk)
        if new_carrier is not None:
            self.decision.set_strategy(new_carrier, self._strategy_bh)

        if new_carrier is None:
            available_robots = self._clear_robot_list(self.data.robots.actives, [self._gk_id])
        else:
            available_robots = self._clear_robot_list(self.data.robots.actives, [self._gk_id, new_carrier.id])

        if not available_robots:
            return

        targets = self._get_defending_positions(avoid=2)

        # TODO: there needs to be a logic for when we don't want to set all non-special robots as defender

        self.decision.calculate_hungarian(
             targets=targets,
             robots=available_robots
        )

    def _use_right_back(self):
        field = self.data.field
        limit = (field.field_width - field.penalty_width) / 2 + 0.5

        return self.data.ball.x < field.field_length / 2 and self.data.ball.y < limit

    def _use_left_back(self):
        field = self.data.field
        limit = (field.field_width + field.penalty_width) / 2 - 0.5

        return self.data.ball.x < field.field_length / 2 and self.data.ball.y > limit

    def _closest_non_keeper(self) -> Optional['TrackedRobot']:
        sq_dist_to_ball = lambda r: np.sum(np.square(np.array(r)-self.data.ball)) \
            if r.id != self._gk_id else np.inf
        my_closest = min(self.data.robots.actives, key=sq_dist_to_ball, default=None)
        return my_closest

    def _get_defending_positions(self, avoid=2):
        targets = []
        max_defenders = max(len(self.data.robots.actives) - avoid, 0)  # -1 for keeper and -1 for ball holder

        # the actual ids of the robots don't matter, we just need to know how many robots we have

        if max_defenders and self._use_left_back():
            targets.extend(LeftBack.decide(self.data, [0]))
            max_defenders -= 1

        if max_defenders and self._use_right_back():
            targets.extend(RightBack.decide(self.data, [0]))
            max_defenders -= 1

        if max_defenders:
            targets.extend(Libero.decide(self.data, list(range(max_defenders))))

        return targets

    def _attacking(self):
        # when in possession, check the ball carrier (smaller time to ball), than it becomes ball carrier
        new_carrier = self._closest_to_ball()

        # the carrier receives its strategies and every other receives its secondary strategies
        for robot in self._robots:
            if robot.robot_id == new_carrier:
                robot.set_strategy(self._strategy_bh)
            else:
                robot.set_strategy(self._secondary_attack_strategies[robot.robot_id])

    def _closest_to_ball(self) -> Optional[int]:
        return self.data.possession.my_closest

    @staticmethod
    def _clear_robot_list(robot_list: list['TrackedRobot'], rm_id: int|list[Optional[int]]) -> list['TrackedRobot']:
        if isinstance(rm_id, int):
            rm_id = [rm_id]

        robot_list = robot_list[:]  # generate a shallow copy to avoid modifying the original list while iterating

        for rm_robot in rm_id:
            if rm_robot is None:
                continue

            for robot in robot_list:
                if robot.id == rm_robot:
                    robot_list.remove(robot)

        return robot_list
