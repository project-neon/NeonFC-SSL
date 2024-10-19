from neonfc_ssl.path_planning.drunk_walk.obstacle import Obstacle
from typing import Tuple, Optional


def line_line_intersection(start_l1, end_l1, start_l2, end_l2):
    ...


def line_rect_intersection(start, end, v1, v2, v3, v4):
    ...


# Static obstacle: will be considered a rectangle, so its vertices will be stored. Collision checking will be simpler
class StaticObstacle(Obstacle):
    def check_for_collision(self):
        ...
