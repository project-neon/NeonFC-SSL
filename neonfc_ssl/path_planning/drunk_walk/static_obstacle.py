from neonfc_ssl.path_planning.drunk_walk.obstacle import Obstacle
from typing import Tuple, Optional


# Static obstacle: will be considered a rectangle, so its vertices will be stored. Collision checking will be simpler
class StaticObstacle(Obstacle):
    start: Tuple[float, float] = None
    length: float = None
    height: float = None
    end = Tuple((start[0] + length, start[1] + height))


    def check_for_collision(self, point, time_step):
        return self.start[0] <= point[0] <= self.end[0] and self.start[1] <= point[1] <= self.end[1]
