import math

from neonfc_ssl.skills import *
from neonfc_ssl.strategies.base_strategy import BaseStrategy


class Test(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Test', coach, match)

        self.field = self._match.field
        self.target = None

        self.states = {
            'move_to_pose_1': MoveToPose(coach, match),
            'move_to_pose_2': MoveToPose(coach, match)
        }

        self.states['move_to_pose_1'].add_transition(self.states['move_to_pose_2'],
                                                     self.states['move_to_pose_1'].complete)
        self.states['move_to_pose_2'].add_transition(self.states['move_to_pose_1'],
                                                     self.states['move_to_pose_2'].complete)

        self.on_one = True

    def _start(self):
        self.active = self.states['move_to_pose_1']
        self.active.start(self._robot, target=(2.4, 0.775, math.pi / 2))
        self.active.start(self._robot, target=(2, 1, math.pi / 2))

    def decide(self):
        next = self.active.update()
        if next != self.active:
            self.on_one = not self.on_one
            self.active.start(self._robot, target=(2.4, 0.3, math.pi / 2) if self.on_one else (2, 1, -math.pi / 2))
        return self.active.decide()
