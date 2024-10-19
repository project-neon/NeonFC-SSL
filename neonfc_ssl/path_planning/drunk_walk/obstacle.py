from dataclasses import dataclass
from abc import ABC, abstractmethod


# Obstacle: has check_for_collision method, receive line segment and return the time of the first collision
@dataclass
class Obstacle(ABC):
    @abstractmethod
    def check_for_collision(self):
        raise NotImplementedError("Implement this method >:(")
