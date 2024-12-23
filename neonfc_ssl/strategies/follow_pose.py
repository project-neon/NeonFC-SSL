from neonfc_ssl.strategies.base_strategy import BaseStrategy
from neonfc_ssl.skills import *
from math import atan2
from dataclasses import dataclass


@dataclass
class Pose:
    x: float
    y: float
    theta: float

    def __getitem__(self, key):
        if isinstance(key, slice):
            # Get the start, stop, and step from the slice
            return [self[ii] for ii in range(*key.indices(3))]
        elif isinstance(key, int):
            if key == 0:
                return self.x

            if key == 1:
                return self.y

            if key == 2:
                return self.theta

    def update(self, values):
        self.x = values[0]
        self.y = values[1]
        self.theta = 0


class FollowPose(BaseStrategy):
    Pose = Pose

    def __init__(self, coach, match):
        super().__init__('Follow Pose', coach, match)
        self.field = self._match.field
        self.skill = MoveToPose(coach, match)

    def _start(self):
        self.skill.start(self._robot, target=self._coach.hungarian_targets[self._robot.robot_id])

    def decide(self):
        return self.skill.decide()
