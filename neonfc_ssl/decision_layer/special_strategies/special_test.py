import math
from neonfc_ssl.decision_layer.skills import *
from neonfc_ssl.decision_layer.special_strategies.special_strategy import SpecialStrategy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData
    from ..skills.base_skill import BaseSkill


class SpecialTest(SpecialStrategy):
    def __init__(self, logger):
        super().__init__(logger)
        self.target = None

        self.states: dict[str, 'BaseSkill'] = {
            'move_to_pose_1': MoveToPose(self.logger, SpecialTest.__name__),
            'move_to_pose_2': MoveToPose(self.logger, SpecialTest.__name__)
        }

        self.states['move_to_pose_1'].add_transition(self.states['move_to_pose_2'],
                                                     self.states['move_to_pose_1'].complete)
        self.states['move_to_pose_2'].add_transition(self.states['move_to_pose_1'],
                                                     self.states['move_to_pose_2'].complete)

        self.on_one = True

    def _start(self):
        self.active = self.states['move_to_pose_1']
        self.active.start(self._robot_id, target=(2.4, 0.775, math.pi / 2))
        self.active.start(self._robot_id, target=(2, 1, math.pi / 2))

    def decide(self, data):
        next = self.active.update(data)
        if next != self.active:
            self.on_one = not self.on_one
            self.active.start(self._robot_id, target=(2.4, 0.3, math.pi / 2) if self.on_one else (2, 1, -math.pi / 2))
        return self.active.decide(data)
