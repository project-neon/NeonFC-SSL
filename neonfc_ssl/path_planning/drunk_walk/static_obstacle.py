from neonfc_ssl.path_planning.drunk_walk.obstacle import Obstacle
from dataclasses import dataclass
from typing import Tuple
import numpy as np


# Static obstacle: will be considered a rectangle, so its vertices will be stored. Collision checking will be simpler
@dataclass
class StaticObstacle(Obstacle):
    start: np.ndarray = np.array((0, 0))
    length: float = 0
    height: float = 0
    end = np.array((start[0] + length, start[1] + height))


    def get_vector(self, origin: np.ndarray) -> np.ndarray:
        dx = max(self.start[0] - origin[0], 0, origin[0] - self.end[0])
        dy = max(self.start[1] - origin[1], 0, origin[1] - self.end[1])
        return np.array((dx, dy))


    def distance_to(self, point: np.ndarray) -> float:
        dx = max(self.start[0] - point[0], 0, point[0] - self.end[0])
        dy = max(self.start[1] - point[1], 0, point[1] - self.end[1])
        return np.sqrt(dx**2 + dy**2)


    # Only works for rectangular obstacles aligned with the x and y axes.
    def check_for_collision(self, point: np.ndarray, time_step: float) -> bool:
        return self.start[0] <= point[0] <= self.end[0] and self.start[1] <= point[1] <= self.end[1]
