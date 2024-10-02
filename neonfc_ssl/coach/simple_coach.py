import math
from neonfc_ssl.coach import BaseCoach
from neonfc_ssl.strategies import Receiver, BallHolder, GoalKeeper, Libero
import numpy as np


class Coach(BaseCoach):
    NAME = "SimpleCoach"

    def _start(self):
        self._strategy_gk = GoalKeeper(self, self._match)
        self._gk_id = 0
        self._strategy_lb = Libero(self, self._match)

        self._strategies_attack = {robot.robot_id: Receiver(self, self._match) for robot in self._match.robots[:-1]}
        self._strategies_attack[self._match.robots[-1].robot_id] = BallHolder(self, self._match)
        self._ball_carrier_id = self._match.robots[-1].robot_id

        self._had_possession = False

    def decide(self):
        if self.has_possession:
            self._attacking()
        else:
            self._defending()

        # for robot in self._match.robots:
        #     print(f"id {robot.robot_id}, stat {robot.strategy.name}")

    def _defending(self):
        attacker = self._closest_non_keeper()

        for robot in self._active_robots:
            if robot.robot_id == self._gk_id:
                robot.set_strategy(self._strategy_gk)
            elif attacker == robot:
                robot.set_strategy(self._strategies_attack[self._ball_carrier_id])
            else:
                robot.set_strategy(self._strategy_lb)

    def _closest_non_keeper(self):
        sq_dist_to_ball = lambda r: np.sum(np.square(np.array(r)-self._match.ball)) \
            if r.robot_id != self._gk_id else np.inf
        my_closest = min(self._match.active_robots, key=sq_dist_to_ball, default=None)
        return my_closest

    def _attacking(self):
        new_carrier = None

        if not self._had_possession:
            new_carrier = self._closest_to_ball()
            # self._had_possession = True
        else:
            if event := self.events.pop('Ball Holder', None):
                new_carrier = event['target']

        if new_carrier is not None:
            temp_s = self._strategies_attack[new_carrier]
            self._strategies_attack[new_carrier] = self._strategies_attack[self._ball_carrier_id]
            self._strategies_attack[self._ball_carrier_id] = temp_s
            self._ball_carrier_id = new_carrier

            for robot in self._active_robots:
                if robot.robot_id == self._gk_id and robot.robot_id != self._ball_carrier_id:
                    robot.set_strategy(self._strategy_gk)
                else:
                    robot.set_strategy(self._strategies_attack[robot.robot_id])

    def _closest_to_ball(self):
        return self._match.possession.current_closest.robot_id
