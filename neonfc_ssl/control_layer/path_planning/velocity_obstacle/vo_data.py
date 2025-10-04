import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class VOType(Enum):
    VO = auto()
    RVO = auto()
    HRVO = auto()


@dataclass
class Obstacle:
    pos: NDArray[np.float64]
    vel: NDArray[np.float64]
    radius: float
    priority: Optional[int] = None

    def __post_init__(self):
        self.pos = np.array(self.pos)
        self.vel = np.array(self.vel)

        if self.priority is None:
            self.priority = 0


@dataclass
class Cone:
    base: NDArray[np.float64]
    dist: float
    radius: float
    left_angle: float
    right_angle: float
