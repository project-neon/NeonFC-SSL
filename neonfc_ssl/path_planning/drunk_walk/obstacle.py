from dataclasses import dataclass
from abc import ABC, abstractmethod


# Obstacle: has check_for_collision method, receive line segment and return the time of the first collision
@dataclass
class Obstacle(ABC):
    @abstractmethod
    def get_vector(self, origin):
        raise NotImplementedError("Here goes the vector (8, D)")
    

    @abstractmethod
    def distance_to(self, point):
        raise NotImplementedError("Of course")


    @abstractmethod
    def check_for_collision(self):
        raise NotImplementedError("There is a collision, you can trust me :)")
