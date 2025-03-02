import math
from neonfc_ssl.decision_layer.skills import *
from neonfc_ssl.decision_layer.special_strategies.special_strategy import SpecialStrategy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..skills.base_skill import BaseSkill


class Passer(SpecialStrategy):
    def __init__(self):
        super().__init__()
        self.target = None
        self.states: dict[str, 'BaseSkill'] = {
            'go_to_ball': GoToBall(),
            'pass': SimplePass()
        }

        self.states['go_to_ball'].add_transition(self.states['pass'], SimplePass.start_pass)
        self.states['pass'].add_transition(self.states['go_to_ball'], SimplePass.stop_pass)

    def _start(self):
        self.active = self.states['go_to_ball']
        self.active.start(self._robot_id)

    def decide(self, data):
        target = data.opposites.active

        next = self.active.update(data)
        if next != self.active:
            self.active = next
            self.active.start(self._robot_id, target=target)
        return self.active.decide(data)
