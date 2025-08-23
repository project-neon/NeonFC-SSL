from ..base_planner import BasePathPlanner
from typing import List, Tuple
from . import Node
from . import RRT


class RRTPlanner(BasePathPlanner):
    def __init__(self, step_size=0.05, max_iter=5000, collision_margin=0.18):
        super().__init__()
        self.step_size = step_size
        self.max_iter = max_iter
        self.collision_margin = collision_margin
        self.node_list = []

    def set_start(self, start: Tuple[float, float]):
        self.start = Node(*start)

    def set_goal(self, goal: Tuple[float, float]):
        self.goal = Node(*goal)

    def set_obstacles(self, obstacles: List):
        self.obstacles = obstacles

    def set_map_area(self, map_area: Tuple[float, float]):
        self.map_area = map_area

    def plan(self) -> List[Tuple[float, float]]:
        # Implementation using the RRT class from the provided code
        rrt = RRT(
            start=(self.start.x, self.start.y),
            goal=(self.goal.x, self.goal.y),
            obstacles=self.obstacles,
            map_area=self.map_area,
            collision_margin=self.collision_margin,
            step_size=self.step_size,
            max_iter=self.max_iter
        )
        self.path = rrt.plan()
        return self.path

    def update(self, current_state, *args, **kwargs):
        # RRT is a global planner, so update is not be needed
        pass