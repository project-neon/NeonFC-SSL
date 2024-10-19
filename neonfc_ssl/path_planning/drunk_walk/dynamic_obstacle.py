from neonfc_ssl.path_planning.drunk_walk.obstacle import Obstacle
from dataclasses import dataclass
from typing import Tuple, Optional
import math


# Dynamic obstacle: will be considered a circle, so its center and radius will be stored along with its speed.
#    Collision check will take into consideration 
@dataclass
class DynamicObstacle(Obstacle):
    center: Tuple[float, float] = None, None
    radius: float = None
    dynamic_radius: float = None
    speed: Tuple[float, float] = None, None

    x, y = center
    vx, vy = speed


    def check_for_collision(self):
        ...


    def distanceTo(self, point: Tuple[float, float]):
        return math.sqrt( ( point[0] - self.x )**2 + ( point[1] - self.y )**2 )


    def get_extra_margin(self):
        ...
