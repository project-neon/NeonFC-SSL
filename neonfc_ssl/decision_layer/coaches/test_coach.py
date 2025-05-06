from .base_coach import Coach
from ..special_strategies import BallHolder, GoalKeeper
from ..positional_strategies import Libero


class TestCoach(Coach):
    def _start(self):
        self.keeper = GoalKeeper()
        self.ballholder = BallHolder()

    def __call__(self, data):
        liberos = data.robots[0:4]

        self.decision.calculate_hungarian(
            targets=Libero.decide(data, [r.id for r in liberos]),
            robots=liberos
        )
