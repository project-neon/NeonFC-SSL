import math

from neonfc_ssl.skills import *
from neonfc_ssl.strategies.base_strategy import BaseStrategy


class Passer(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Passer', coach, match)

        self.field = self._match.field
        self.target = None

        self.states = {
            'go_to_ball': GoToBall(coach, match),
            'pass': SimplePass(coach, match)
        }

        def not_func(f):
            def wrapped():
                return not f()

            return wrapped

        self.states['go_to_ball'].add_transition(self.states['pass'], self.states['go_to_ball'].complete)
        # self.states['pass'].add_transition(self.states['go_to_ball'], not_func(self.states['go_to_ball'].complete))

    def _start(self):
        self.active = self.states['go_to_ball']
        self.active.start(self._robot)

    def decide(self):
        target = self._match.active_opposites[0]

        next = self.active.update()
        if next != self.active:
            self.active = next
            self.active.start(self._robot, target=target)
        return self.active.decide()
