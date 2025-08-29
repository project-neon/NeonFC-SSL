from ..base_planner import BasePathPlanner
from typing import List, Tuple
from . import Node, RRT, RRTStar


class RRTPlanner(BasePathPlanner):
    def __init__(self, step_size=0.1, max_iter=5000, collision_margin=0.18):
        super().__init__()
        self.step_size = step_size
        self.max_iter = max_iter
        self.collision_margin = collision_margin
        self.obstacles = []  # Store obstacles as Node objects

    def set_start(self, start: Tuple[float, float]):
        self.start = start

    def set_goal(self, goal: Tuple[float, float]):
        self.goal = goal

    def set_speed(self, speed: Tuple[float, float]):
        self.speed = speed

    def set_obstacles(self, obstacles: List):
        # Convert obstacles to Node objects
        self.obstacles = [Node(obs[0], obs[1]) for obs in obstacles]

    def set_map_area(self, map_area: Tuple[float, float]):
        self.map_area = map_area

    def plan(self) -> List[Tuple[float, float]]:
        rrt = RRT(
            start=self.start,
            goal=self.goal,
            obstacles=self.obstacles,
            map_area=self.map_area,
            collision_margin=self.collision_margin,
            step_size=self.step_size,
            max_iter=self.max_iter
        )

        path = rrt.plan()

        self.path = path if path else [[self.start[0] + self.step_size * self.speed[0],
                                       self.start[1] + self.step_size * self.speed[1]]]

        return self.path

    def update(self, current_state, *args, **kwargs):
        # RRT is a global planner, so update is not needed
        pass

    def get_path(self):
        return self.path

    @staticmethod
    def create_rectangle_obstacles(center, width, height, density=0.1):
        """Convert rectangular area into discrete obstacle points"""
        obstacles = []
        x_start = center[0] - width / 2
        x_end = center[0] + width / 2
        y_start = center[1] - height / 2
        y_end = center[1] + height / 2

        x = x_start
        while x <= x_end:
            y = y_start
            while y <= y_end:
                obstacles.append((x, y))
                y += density
            x += density

        return obstacles


class RRTStarPlanner(BasePathPlanner):
    def __init__(self, step_size=0.1, max_iter=5000, collision_margin=0.18):
        super().__init__()
        self.step_size = step_size
        self.max_iter = max_iter
        self.collision_margin = collision_margin
        self.obstacles = []  # Store obstacles as Node objects

    def set_start(self, start: Tuple[float, float]):
        self.start = start

    def set_goal(self, goal: Tuple[float, float]):
        self.goal = goal

    def set_speed(self, speed: Tuple[float, float]):
        self.speed = speed

    def set_obstacles(self, obstacles: List):
        # Convert obstacles to Node objects
        self.obstacles = [Node(obs[0], obs[1]) for obs in obstacles]

    def set_map_area(self, map_area: Tuple[float, float]):
        self.map_area = map_area

    def plan(self) -> List[Tuple[float, float]]:
        rrt_star = RRTStar(
            start=self.start,
            goal=self.goal,
            obstacles=self.obstacles,
            map_area=self.map_area,
            collision_margin=self.collision_margin,
            step_size=self.step_size,
            max_iter=self.max_iter
        )
        path = rrt_star.plan()

        self.path = path if len(path) > 0 else [[self.start[0] + self.step_size * self.speed[0],
                                                 self.start[1] + self.step_size * self.speed[1]]]

        return self.path

    def update(self, current_state, *args, **kwargs):
        # RRT* is a global planner, so update is not needed
        pass

    def get_path(self):
        return self.path

    @staticmethod
    def create_rectangle_obstacles(center, width, height, density=0.1):
        """Convert rectangular area into discrete obstacle points"""
        obstacles = []
        x_start = center[0] - width / 2
        x_end = center[0] + width / 2
        y_start = center[1] - height / 2
        y_end = center[1] + height / 2

        x = x_start
        while x <= x_end:
            y = y_start
            while y <= y_end:
                obstacles.append((x, y))
                y += density
            x += density

        return obstacles
