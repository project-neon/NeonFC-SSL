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
             walls: List[Tuple] = None,
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
        self.walls = walls or []
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

    @staticmethod
    def _point_to_segment_distance(px: float, py: float,
                                   ax: float, ay: float,
                                   bx: float, by: float) -> float:
        """Returns the shortest distance from point P to segment AB.

        Projects P onto the line defined by AB, then clamps the projection
        parameter t to [0, 1] so the closest point stays within the segment.
        This avoids the false-positive collisions that arise from treating
        the segment as an infinite line.
        """
        dx, dy = bx - ax, by - ay
        seg_len_sq = dx * dx + dy * dy

        if seg_len_sq == 0:
            # Degenerate segment (A == B): distance is just point-to-point.
            return math.sqrt((px - ax) ** 2 + (py - ay) ** 2)

        # t is how far along AB the projection of P falls.
        t = ((px - ax) * dx + (py - ay) * dy) / seg_len_sq
        t = max(0.0, min(1.0, t))   # Clamp to segment bounds

        closest_x = ax + t * dx
        closest_y = ay + t * dy

        return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)

    @staticmethod
    def _segments_intersect(ax: float, ay: float, bx: float, by: float,
                            cx: float, cy: float, dx: float, dy: float) -> bool:
        """Returns True if segment AB intersects segment CD.

        Uses parametric form: any point on AB = A + t*(B-A), t in [0,1],
        and any point on CD = C + u*(D-C), u in [0,1]. Solves for t and u
        via the 2D cross product; parallel segments (zero denominator) never
        intersect.
        """
        ab_x, ab_y = bx - ax, by - ay
        cd_x, cd_y = dx - cx, dy - cy
        ca_x, ca_y = ax - cx, ay - cy

        denom = ab_x * cd_y - ab_y * cd_x
        if denom == 0:
            return False    # Parallel segments.

        t = (ca_x * cd_y - ca_y * cd_x) / denom
        u = (ca_x * ab_y - ca_y * ab_x) / denom

        return 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0

    def is_collision_free(self, start: Node, end: Node) -> bool:
        """Checks whether the segment start→end is free of collisions.

        Two types of obstacles are checked:
        - Point obstacles (robots): uses point-to-segment distance with
          collision_margin as the minimum clearance radius.
        - Wall segments (field boundaries, penalty areas): uses exact
          segment-segment intersection, so no discretisation is needed.
        """
        # --- Point obstacles (robots) ---
        for obs in self.obstacles:
            dist = self._point_to_segment_distance(
                obs.x, obs.y,
                start.x, start.y,
                end.x, end.y
            )
            if dist < self.collision_margin:
                return False

        # --- Wall segments (field boundaries and penalty areas) ---
        for wall in self.walls:
            (cx, cy), (dx, dy) = wall
            if self._segments_intersect(
                start.x, start.y, end.x, end.y,
                cx, cy, dx, dy
            ):
                return False

        return True

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
            else:
                continue

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
            else:
                continue

            if d := math.sqrt((new_node.x - self.goal.x)**2 + (new_node.y - self.goal.y)**2) <= self.step_size:
                if self.is_collision_free(new_node, self.goal):
                    self.goal.parent = new_node
                    self.goal.cost = new_node.cost + d
                    self.node_list.append(self.goal)

                    return self.generate_final_path()

        return []
