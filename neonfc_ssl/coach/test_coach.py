from neonfc_ssl.coach import BaseCoach
# from strategies.follow_ball import FollowBall
from neonfc_ssl.strategies import SoloAttacker, SimplePasser, Still


class Coach(BaseCoach):
    NAME = "TestCoach"

    def __init__(self, match):
        super().__init__(match)

    def decide(self):
        self._robots[0].set_strategy(SimplePasser)
        self._robots[1].set_strategy(Still)
