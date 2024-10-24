from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np


# Obstacle: has check_for_collision method, receive line segment and return the time of the first collision
@dataclass
class Obstacle(ABC):
    @abstractmethod
    def get_vector(self, origin: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Here goes the vector (8, D)")
    

    @abstractmethod
    def distance_to(self, point: np.ndarray) -> float:
        raise NotImplementedError("Of course")


    @abstractmethod
    def check_for_collision(self, point: np.ndarray, time_step: float) -> bool:
        raise NotImplementedError("There is a collision, you can trust me :)")
