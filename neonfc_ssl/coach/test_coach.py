import math
from neonfc_ssl.coach import BaseCoach
from neonfc_ssl.strategies import Receiver, BallHolder, Test, GoalKeeper, Passer, Libero


class Coach(BaseCoach):
    NAME = "TestCoach"

    def _start(self):
        self.test = GoalKeeper(self, self._match)
        self.test2 = Libero(self, self._match)

    def decide(self):
        self._active_robots[0].set_strategy(self.test)
        self._active_robots[1].set_strategy(self.test2)
