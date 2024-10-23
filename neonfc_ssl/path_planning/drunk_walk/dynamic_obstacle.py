from neonfc_ssl.path_planning.drunk_walk.obstacle import Obstacle
from dataclasses import dataclass
from typing import Tuple
import numpy as np
import math


# Dynamic obstacle: will be considered a circle, so its center and radius will be stored along with its speed.
#    Collision check will take into consideration 
@dataclass
class DynamicObstacle(Obstacle):
    center: Tuple[float, float] = Tuple((None, None))
    radius: float = None
    dynamic_radius: float = None
    speed: Tuple[float, float] = Tuple((None, None))

    x, y = center
    vx, vy = speed


    def get_vector(self, origin: np.ndarray):
        return np.array(self.center) - origin
    

    def distance_to(self, point: Tuple[float, float]):
        return math.sqrt( ( point[0] - self.x )**2 + ( point[1] - self.y )**2 )


    def check_for_collision(self, point, time_step):
        return self.distanceTo(point) < self.radius + self.get_extra_margin(time_step)


    def get_extra_margin(self, time_step):
        ...
