import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass
from enum import Enum, auto


class VOType(Enum):
    VO = auto()
    RVO = auto()
    HRVO = auto()


@dataclass
class Obstacle:
    pos: NDArray[np.float64]
    vel: NDArray[np.float64]
    radius: float
    priority: int


@dataclass
class Cone:
    base: NDArray[np.float64]
    dist: float
    radius: float
    left_angle: float
    right_angle: float
