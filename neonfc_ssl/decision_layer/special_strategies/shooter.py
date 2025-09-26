from neonfc_ssl.decision_layer.skills import *
from neonfc_ssl.decision_layer.special_strategies.special_strategy import (
    SpecialStrategy,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..skills.base_skill import BaseSkill


class Shooter(SpecialStrategy):
    def __init__(self, logger):
        super().__init__(logger)
        self.target = None
        self.states: dict[str, "BaseSkill"] = {
            "go_to_ball": GoToBall(self.logger, Shooter.__name__),
            "shoot": Shoot(self.logger, Shooter.__name__),
        }

        self.states["go_to_ball"].add_transition(
            self.states["shoot"], Shoot.start_shoot
        )
        self.states["shoot"].add_transition(self.states["go_to_ball"], Shoot.stop_shoot)

    def _start(self):
        self.active = self.states["go_to_ball"]
        self.active.start(self._robot_id)

    def decide(self, data):
        next = self.active.update(robot=data.robots[self._robot_id], ball=data.ball)
        if next != self.active:
            self.active = next
            self.active.start(self._robot_id)

        return self.active.decide(data)
