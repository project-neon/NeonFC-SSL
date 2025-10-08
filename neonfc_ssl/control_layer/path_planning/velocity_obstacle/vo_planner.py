from ..base_planner import Planner
from typing import List, Tuple
from .vo import StarVO
import numpy as np


class VOPlanner(Planner):
    def __init__(self):
        super().__init__()
        self.star_vo = StarVO(
            pos=(0,0),
            goal=(0,0),
            vel=(0,0)
        )

    def set_start(self, start: Tuple[float, float]):
        self.start = start
        self.star_vo.pos = np.array(start, dtype=np.float64)

    def set_goal(self, goal: Tuple[float, float]):
        self.goal = goal
        self.star_vo.goal = np.array(goal, dtype=np.float64)

    def set_velocity(self, velocity: Tuple[float, float]):
        self.velocity = velocity
        self.star_vo.vel = np.array(velocity, dtype=np.float64)

    def set_obstacles(self, obstacles: List):
        if not obstacles: return
        self.obstacles.extend(obstacles)
        dynamic_obstacles = [([o[0], o[1]], np.zeros(2), 0.09) for o in obstacles]
        self.star_vo.update_dynamic_obstacles(dynamic_obstacles)

    def set_walls(self, walls: List):
        if not walls: return
        self.obstacles.extend(walls)
        self.star_vo.update_walls(walls)

    def set_map_area(self, map_area: Tuple[float, float]):
        pass

    def plan(self) -> List[float]:
        self.path = self.star_vo.pos + self.star_vo.update()
        return self.path.tolist()

    def update(self, current_state, *args, **kwargs):
        pass

    def get_path(self):
        return self.path

    def add_field_walls(self, origin, length, width, border=0.3, avoid_area: bool =False):
        x_min = origin - border
        y_min = origin - border
        x_max = origin + length + border
        y_max = origin + width + border

        walls = [
            [(x_min, y_min), (x_min, y_max)],
            [(x_min, y_max), (x_max, y_max)],
            [(x_max, y_max), (x_max, y_min)],
            [(x_max, y_min), (x_min, y_min)]
        ]

        area_walls = [
            [(-0.3, width/2 - 1.0), (1.0, width/2 - 1.0)],
            [(-0.3, width/2 + 1.0), (1.0, width/2 + 1.0)],
            [(1.0, width/2 - 1.0), (1.0, width/2 + 1.0)],
            [(length - 1.0, width / 2 - 1.0), (length + 0.3, width / 2 - 1.0)],
            [(length - 1.0, width / 2 + 1.0), (length + 0.3, width / 2 + 1.0)],
            [(length - 1.0, width / 2 - 1.0), (length - 1.0, width / 2 + 1.0)]
        ]

        if avoid_area:
            walls += area_walls

        self.set_walls(walls)