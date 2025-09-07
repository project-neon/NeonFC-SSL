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

    def set_speed(self, speed: Tuple[float, float]):
        self.speed = speed
        self.star_vo.v = np.array(speed, dtype=np.float64)

    def set_obstacles(self, obstacles: List):
        if not obstacles: pass
        self.obstacles.extend(obstacles)
        dynamic_obstacles = [([o[0], o[1]], np.zeros(2), 0.09) for o in obstacles]
        self.star_vo.update_dynamic_obstacles(dynamic_obstacles)

    def set_walls(self, walls: List):
        if not walls: pass
        self.obstacles.extend(walls)
        self.star_vo.update_walls(walls)

    def set_map_area(self, map_area: Tuple[float, float]):
        self.map_area = [6.0, 9.0]

    def plan(self) -> np.ndarray:
        self.path = self.star_vo.update()
        return self.path

    def update(self, current_state, *args, **kwargs):
        pass

    def get_path(self):
        return self.path
