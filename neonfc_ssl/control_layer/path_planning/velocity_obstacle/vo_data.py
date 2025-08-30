import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass


@dataclass
class Obstacle:
    pos: NDArray[np.float64]
    vel: NDArray[np.float64]
    radius: float
    priority: int


@dataclass
class Wall:
    start: NDArray[np.float64]
    end: NDArray[np.float64]


@dataclass
class Cone:
    base: NDArray[np.float64]
    dist: float
    radius: float
    left_angle: float
    right_angle: float
