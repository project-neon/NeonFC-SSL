from typing import Tuple


def line_line_intersection(start_l1, end_l1, start_l2, end_l2):
    ...


def line_circle_intersection(start, end, center, radius):
    ...


class DrunkWalk:
    def __init__(self) -> None:
        self.pos: Tuple[float, float, float] = None
        self.vel: Tuple[float, float] = None
        self.dest: Tuple[float, float] = None
        self.obstacles: list[Tuple[float, float]] = None    


    def _gen_rnd_subdests(self):
        ...


    def _check_for_collision(self, pos, dest):
        ...
