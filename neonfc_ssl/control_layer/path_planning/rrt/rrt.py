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
             map_area=(9, 6),
             collision_margin=0.18,
             step_size=0.05,
             max_iter=5000
        ):

        self.start = Node(*start)
        self.goal = Node(*goal)
        self.map_area = map_area
        self.step_size = step_size
        self.max_iter = max_iter
        self.obstacles = obstacles
        self.collision_margin = collision_margin
        self.path = None
        self.node_list: List[Node] = [self.start]

    def get_random_node(self):
        x = random.uniform(0, self.map_area[0])
        y = random.uniform(0, self.map_area[1])

        return Node(x, y)

    def get_nearest_node(self, node) -> Node:
        distance_list = [ (node.x - node_i.x)**2 + (node.y - node_i.y)**2 for node_i in self.node_list ]
        min_index = np.argmin(distance_list)

        return self.node_list[min_index]

    def steer(self, start: Node, end: Node) -> Node:

        theta = math.atan2(end.y - start.y, end.x - start.x)

        new_node = Node(
            start.x + self.step_size * math.cos(theta),
            start.y + self.step_size * math.sin(theta)
        )

        new_node.parent = start
        new_node.cost = start.cost + self.step_size

        return new_node

    def is_collision_free(self, start: Node, end: Node) -> bool:
        A = end.y - start.y
        B = start.x - end.x
        C = - A*start.x - B*start.y
        div = math.sqrt(A**2 + B**2)

        sec = lambda o: ( abs( A*o.x + B*o.y + C ) / div ) > self.collision_margin

        return all( sec(obstacle) for obstacle in self.obstacles )

    def generate_final_path(self) -> List[List[float]]:
        path = []
        node = self.goal

        while node is not None:
            path.append([node.x, node.y])
            node = node.parent

        self.path = path

        return path[::-1]

    def plan(self) -> List[List[float]]:

        for _ in range(self.max_iter):

            random_node = self.get_random_node()
            nearest_node = self.get_nearest_node(random_node)

            new_node = self.steer(nearest_node, random_node)

            if self.is_collision_free(nearest_node, new_node):
                self.node_list.append(new_node)
            else: continue

            if d := math.sqrt((new_node.x - self.goal.x)**2 + (new_node.y - self.goal.y)**2) <= self.step_size:
                if self.is_collision_free(new_node, self.goal):
                    self.goal.parent = new_node
                    self.goal.cost = new_node.cost + d
                    self.node_list.append(self.goal)

                    return self.generate_final_path()

        return []


class RRTStar(RRT):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.search_radius = 2.0*self.step_size

    def find_neighbors(self, node):
        return [n for n in self.node_list if np.linalg.norm([n.x - node.x, n.y - node.y]) <= self.search_radius]

    def choose_parent(self, neighbors, nearest, node):
        min_cost = nearest.cost + np.linalg.norm([nearest.x - node.x, nearest.y - node.y])
        best_node = nearest

        for neighbor in neighbors:
            cost = neighbor.cost + np.linalg.norm([neighbor.x - node.x, neighbor.y - node.y])

            if cost < min_cost and self.is_collision_free(neighbor, node):
                min_cost = cost
                best_node = neighbor

        node.cost = min_cost
        node.parent = best_node

        return node

    def rewire(self, node, neighbors):
        for neighbor in neighbors:
            cost = node.cost + np.linalg.norm([neighbor.x - node.x, neighbor.y - node.y])

            if cost < neighbor.cost and self.is_collision_free(neighbor, node):
                neighbor.parent = node
                neighbor.cost = cost

    def plan(self):

        for _ in range(self.max_iter):

            random_node = self.get_random_node()
            nearest_node = self.get_nearest_node(random_node)

            new_node = self.steer(nearest_node, random_node)

            if self.is_collision_free(nearest_node, new_node):
                neighbors = self.find_neighbors(new_node)
                self.choose_parent(neighbors, nearest_node, new_node)
                self.rewire(new_node, neighbors)
                self.node_list.append(new_node)
            else: continue

            if d := math.sqrt((new_node.x - self.goal.x)**2 + (new_node.y - self.goal.y)**2) <= self.step_size:
                if self.is_collision_free(new_node, self.goal):
                    self.goal.parent = new_node
                    self.goal.cost = new_node.cost + d
                    self.node_list.append(self.goal)

                    return self.generate_final_path()

        return []
