import math
import random
import numpy as np
from typing import List, Tuple
from . import Node

class RRT:
    def __init__(self,
            start: Tuple[float, float],
            goal: Tuple[float, float],
            obstacles: List[Node],
            map_area: Tuple[float, float] = (9, 6),
            collision_margin: float = 0.18,
            step_size: float = 0.05,
            max_iter: int = 5000
        ):

        self.start = Node(*start)
        self.goal = Node(*goal)
        self.obstacles = obstacles
        self.map_area = map_area
        self.collision_margin = collision_margin
        self.step_size = step_size
        self.max_iter = max_iter
        self.node_list: List[Node] = [self.start]
        self.path = None

    def get_random_node(self):
        x = random.uniform(0, self.map_area[0])
        y = random.uniform(0, self.map_area[1])
        return Node(x, y)

    def get_nearest_node(self, node):
        distance_list = [(node.x - node_i.x)**2 + (node.y - node_i.y)**2 for node_i in self.node_list]
        min_index = np.argmin(distance_list)
        return self.node_list[min_index]

    def steer(self, start: Node, end: Node):
        theta = math.atan2(end.y - start.y, end.x - start.x)

        new_node = Node(
            start.x + self.step_size * math.cos(theta),
            start.y + self.step_size * math.sin(theta)
        )

        new_node.parent = start
        new_node.cost = start.cost + self.step_size
        return new_node

    def is_collision_free(self, start: Node, end: Node):
        # check bounds first
        if not (0 <= end.x <= self.map_area[0] and 0 <= end.y <= self.map_area[1]):
            return False

        a = end.y - start.y
        b = start.x - end.x
        c = -a * start.x - b * start.y

        # Handle the case where start and end are the same point
        div = math.sqrt(a**2 + b**2)
        if div == 0:
            # Points are identical, check if start point collides with obstacles
            for obstacle in self.obstacles:
                dist = math.sqrt((start.x - obstacle.x)**2 + (start.y - obstacle.y)**2)
                if dist <= self.collision_margin:
                    return False
            return True

        # check line segment collision with obstacles
        for obstacle in self.obstacles:
            # Distance from point to line
            line_dist = abs(a * obstacle.x + b * obstacle.y + c) / div

            if line_dist <= self.collision_margin:
                # check if the closest point on the line is within the segment
                t = ((obstacle.x - start.x) * (end.x - start.x) +
                     (obstacle.y - start.y) * (end.y - start.y)) / (div**2)

                if 0 <= t <= 1:  # closest point is on the segment
                    return False
                else:
                    # check distance to endpoints
                    dist_to_start = math.sqrt((obstacle.x - start.x)**2 + (obstacle.y - start.y)**2)
                    dist_to_end = math.sqrt((obstacle.x - end.x)**2 + (obstacle.y - end.y)**2)

                    if min(dist_to_start, dist_to_end) <= self.collision_margin:
                        return False

        return True

    def generate_path(self):
        path = []
        node = self.goal

        while node is not None:
            path.append([node.x, node.y])
            node = node.parent

        self.path = path
        return path[::-1]

    def plan(self):
        for iteration in range(self.max_iter):
        # while True:

            random_node = self.get_random_node()
            nearest_node = self.get_nearest_node(random_node)

            new_node = self.steer(nearest_node, random_node)

            if self.is_collision_free(nearest_node, new_node):
                self.node_list.append(new_node)

                # check if we can connect to goal
                goal_distance = math.sqrt((new_node.x - self.goal.x)**2 + (new_node.y - self.goal.y)**2)

                if goal_distance <= self.step_size:
                    if self.is_collision_free(new_node, self.goal):
                        self.goal.parent = new_node
                        self.goal.cost = new_node.cost + goal_distance
                        self.node_list.append(self.goal)
                        return self.generate_path()

        # No path found
        return []