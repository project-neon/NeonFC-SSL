from .base_coach import Coach
from ..special_strategies import BallHolder, GoalKeeper, InterceptBall, Passer, Shooter, Still
from ..positional_strategies import Libero, LeftBack, RightBack


class TestCoach(Coach):
    def _start(self):
        self.keeper = GoalKeeper(self.decision.logger)
        self.ballholder = InterceptBall(self.decision.logger)
        self.passer = Passer(self.decision.logger)
        self.shooter = Shooter(self.decision.logger)
        self.wait = Still(self.decision.logger)
        self.last_holder = None

    def decide(self):
        holder = self.data.possession.my_closest
        if holder == self.last_holder:
            return

        if self.last_holder is not None:
            self.decision.set_strategy(self.data.robots[self.last_holder], self.wait)

        self.decision.set_strategy(self.data.robots[holder], self.passer)
        self.last_holder = holder

        # liberos = self.data.robots[0:3]
        # left_backs = self.data.robots[3:4]
        # right_backs = self.data.robots[4:5]

        # targets = [
        #     Libero.decide(self.data, [r.id for r in liberos]),
        #     LeftBack.decide(self.data, [r.id for r in left_backs]),
        #     RightBack.decide(self.data, [r.id for r in right_backs])
        # ]

        # self.decision.calculate_hungarian(
        #     targets=[i for j in targets for i in j],
        #     robots=[i for j in [liberos, left_backs, right_backs] for i in j]
        # )
