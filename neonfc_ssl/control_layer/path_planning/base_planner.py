from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Union
import numpy as np


class BasePathPlanner(ABC):
    def __init__(self):
        self.start = None
        self.goal = None
        self.velocity = None
        self.obstacles = []
        self.map_area = None
        self.path = None

    @abstractmethod
    def set_start(self, start: Tuple[float, float]):
        """Set the start position"""
        raise Exception("Method not implemented!")

    @abstractmethod
    def set_goal(self, goal: Tuple[float, float]):
        """Set the goal position"""
        raise Exception("Method not implemented!")

    @abstractmethod
    def set_velocity(self, velocity: Tuple[float, float]):
        """Set the robot speed"""
        raise Exception("Method not implemented")

    @abstractmethod
    def set_obstacles(self, obstacles: List):
        """Set the obstacles in the environment"""
        raise Exception("Method not implemented!")

    @abstractmethod
    def set_walls(self, walls: List):
        """Set the walls in the environment"""
        raise Exception("Method not implemented!")

    @abstractmethod
    def set_map_area(self, map_area: Tuple[float, float]):
        """Set the map boundaries"""
        raise Exception("Method not implemented!")

    @abstractmethod
    def plan(self, *args, **kwargs) -> Union[List[float], np.ndarray]:
        """Generate a path from start to goal"""
        raise Exception("Method not implemented!")

    @abstractmethod
    def update(self, current_state, *args, **kwargs):
        """Update the planner with new information (for reactive planners)"""
        raise Exception("Method not implemented!")

    def get_path(self) -> Optional[Union[List[Tuple[float, float]], np.ndarray]]:
        """Return the computed path"""
        return self.path

    def clear(self):
        """Reset the planner state"""
        self.start = None
        self.goal = None
        self.obstacles = []
        self.map_area = None
        self.path = None
