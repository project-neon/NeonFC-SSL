from .base_coach import Coach
from ..special_strategies import BallHolder, GoalKeeper,InterceptBall
from ..positional_strategies import Libero, LeftBack, RightBack


class TestCoach(Coach):
    def _start(self):
        self.keeper = GoalKeeper()
        self.ballholder = InterceptBall()

    def __call__(self, data):
        self.decision.set_strategy(data.robots[0], self.ballholder)
        # liberos = data.robots[0:3]
        # left_backs = data.robots[3:4]
        # right_backs = data.robots[4:5]

        # targets = [
        #     Libero.decide(data, [r.id for r in liberos]),
        #     LeftBack.decide(data, [r.id for r in left_backs]),
        #     RightBack.decide(data, [r.id for r in right_backs])
        # ]

        # self.decision.calculate_hungarian(
        #     targets=[i for j in targets for i in j],
        #     robots=[i for j in [liberos, left_backs, right_backs] for i in j]
        # )
