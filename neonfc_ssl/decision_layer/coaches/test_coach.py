from base_coach import Coach
from ..special_strategies import BallHolder, GoalKeeper
from ..positional_strategies import Libero


class TestCoach(Coach):
    def _start(self):
        self.keeper = GoalKeeper()
        self.ballholder = BallHolder()

    def __call__(self, data):
        self.decision.set_strategy(data.robots.actives[0], self.ballholder)

        n = len(data.robots.actives) - 1
        liberos = data.robots[1:n+1]

        self.decision.calculate_hungarian(
            targets=Libero.decide(data, [r.id for r in liberos]),
            robots=liberos
        )
