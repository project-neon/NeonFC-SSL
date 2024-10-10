import math
from neonfc_ssl.coach import BaseCoach
from neonfc_ssl.strategies import BaseStrategy, Receiver, BallHolder, GoalKeeper, Libero, Still
import numpy as np


class Coach(BaseCoach):
    NAME = "SimpleCoach"

    def _start(self):
        # Create strategies objects

        # Especial cases
        self._strategy_gk = GoalKeeper(self, self._match)
        self._strategy_bh = BallHolder(self, self._match)
        self._gk_id = 0

        # Default attack strategies
        self._secondary_attack_strategies: dict[int, BaseStrategy] = {
            robot.robot_id: Receiver(self, self._match) for robot in self._match.robots if robot.robot_id != self._gk_id
        }
        self._secondary_attack_strategies[self._gk_id] = self._strategy_gk

        # Default defense strategies
        self._secondary_defense_strategies: dict[int, BaseStrategy] = {
            robot.robot_id: Libero(self, self._match) for robot in self._match.robots if robot.robot_id != self._gk_id
        }
        self._secondary_defense_strategies[self._gk_id] = self._strategy_gk

    def decide(self):
        if self.has_possession:
            self._attacking()
        else:
            self._defending()

    def _defending(self):
        # when in possession check the ball carrier (smaller time to ball), than it becomes ball carrier
        new_carrier = self._closest_non_keeper()

        # the carrier receives its strategies and every other receives its secondary strategies
        for robot in self._robots:
            if robot.robot_id == new_carrier:
                robot.set_strategy(self._strategy_bh)
            else:
                robot.set_strategy(self._secondary_defense_strategies[robot.robot_id])

    def _closest_non_keeper(self):
        sq_dist_to_ball = lambda r: np.sum(np.square(np.array(r)-self._match.ball)) \
            if r.robot_id != self._gk_id else np.inf
        my_closest = min(self._match.active_robots, key=sq_dist_to_ball, default=None)
        return my_closest.robot_id

    def _attacking(self):
        # when in possession check the ball carrier (smaller time to ball), than it becomes ball carrier
        new_carrier = self._closest_to_ball()

        # the carrier receives its strategies and every other receives its secondary strategies
        for robot in self._robots:
            if robot.robot_id == new_carrier:
                robot.set_strategy(self._strategy_bh)
            else:
                robot.set_strategy(self._secondary_attack_strategies[robot.robot_id])

    def _closest_to_ball(self):
        return self._match.possession.current_closest.robot_id
