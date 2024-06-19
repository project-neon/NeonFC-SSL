import math
from neonfc_ssl.coach import BaseCoach
from neonfc_ssl.strategies import Receiver, BallHolder


class Coach(BaseCoach):
    NAME = "TestCoach"

    def _start(self):
        self._strategies_attack = {robot.robot_id: Receiver(self, self._match) for robot in self._match.robots[:-1]}
        self._strategies_attack[self._match.robots[-1].robot_id] = BallHolder(self, self._match)
        self._ball_carrier_id = self._match.robots[-1].robot_id
        self._had_possession = False

    def decide(self):
        if self.has_possession:
            self._attacking()
        else:
            self._attacking()

    def _attacking(self):
        new_carrier = None

        if not self._had_possession:
            new_carrier = self._closest_to_ball()
            self._had_possession = True
        else:
            if event := self.events.pop('Ball Holder', None):
                new_carrier = event['target']

        if new_carrier is not None:
            temp_s = self._strategies_attack[new_carrier]
            self._strategies_attack[new_carrier] = self._strategies_attack[self._ball_carrier_id]
            self._strategies_attack[self._ball_carrier_id] = temp_s
            self._ball_carrier_id = new_carrier

            for robot in self._active_robots:
                robot.set_strategy(self._strategies_attack[robot.robot_id])

    def _closest_to_ball(self):
        ball = self._match.ball
        dists = [(r, math.sqrt((r.x-ball.x)**2 + (r.y-ball.y)**2)) for r in self._active_robots]
        return min(dists, key=lambda x: x[1])[0].robot_id
