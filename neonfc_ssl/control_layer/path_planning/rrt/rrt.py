import math
import random
import numpy as np
from typing import Tuple, List
from . import Node

class RRT:
    def __init__(
            self,
            start: Tuple[float],
            goal: Tuple[float],
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
        self.node_list = [self.start]
        self.path = None

    def get_random_node(self):
        x = random.uniform(0, self.map_area[0])
        y = random.uniform(0, self.map_area[1])

        return Node(x, y)

    def get_nearest_node(self, node: Node):
        distances = [ (node.x - node_i.x)**2 + (node.y - node_i.y)**2 for node_i in self.node_list ]
        min_index = np.argmin(distances)

        return self.node_list[min_index]

    def steer(self, from_node: Node, to_node: Node):
        theta = math.atan2(to_node.y - from_node.y, to_node.x - from_node.x)

        new_node = Node(
            from_node.x + self.step_size * math.cos(theta),
            from_node.y + self.step_size * math.sin(theta)
        )

        new_node.parent = from_node
        new_node.cost = from_node.cost + self.step_size

        return new_node

    def is_collision_free(self, p1: Node, p2: Node):
        a = p2.y - p1.y
        b = p1.x - p2.x
        c = - a*p1.x - b*p1.y
        div = math.sqrt(a**2 + b**2)

        sec = lambda o: ( abs( a*o.x + b*o.y + c ) / div ) > self.collision_margin

        return all(sec(obstacle) for obstacle in self.obstacles)

    def generate_path(self):
        final_path = []
        cur_node = self.goal

        while cur_node is not None:
            final_path.append([cur_node.x, cur_node.y])
            cur_node = cur_node.parent

        return final_path[::-1]

    def plan(self):

        # for _ in range(self.max_iter):
        while True:

            random_node = self.get_random_node()
            nearest_node = self.get_nearest_node(random_node)

            new_node = self.steer(nearest_node, random_node)

            if self.is_collision_free(nearest_node, new_node):
                self.node_list.append(new_node)
            else: continue

            print(new_node, self.goal)

            if d := math.sqrt((new_node.x - self.goal.x)**2 + (new_node.y - self.goal.y)**2) <= self.step_size:
                if self.is_collision_free(new_node, self.goal):
                    self.goal.parent = new_node
                    self.goal.cost = new_node.cost + d
                    self.node_list.append(self.goal)

                    return self.generate_path()

        return []


if __name__ == "__main__":
    ...