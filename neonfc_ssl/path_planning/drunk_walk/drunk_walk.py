from typing import Tuple
from neonfc_ssl.path_planning.drunk_walk.obstacle import Obstacle
import numpy as np


def array2tuple(array: np.ndarray):
    return tuple(map(float, array))


'''
1. Generate obstacles that can be either static or dynamic ones.
requirements:
    obstacle dataclasses: dynamic obstacle and static obstacle
        Obstacle: has check_for_collision method, receive line segment and return the distance of the first collision
        Static obstacle: will be considered a rectangle, so its vertices will be stored. Collision checking will be simpler
        Dynamic obstacle: will be considered a circle, so its center and radius will be stored along with its speed.
            Collision check will take into consideration 

2. Adapt the input to fit the algorithm. There are 2 cases that needs attention:
    - If the target point overlaps with an obstacle, move it to the closest point outside the obstacle.
    - If the robot position overlaps with an obstacle, just remove the obstacle from the list.

3. Find a path. 
By either going directly to the target, if possible, or by generating random subdestinations. As the algorithm proposes.
Sometimes it is not possible to find an optimal path, in those cases, return the rejected path with the highest collision dist.

4. Execute the trajectory, adapting it for the control we have, instead of returning the full path,
it will return a point of the chosen trajectory with fixed distance.
'''


class DrunkWalk:
    def __init__(self) -> None:
        self._pos: np.ndarray = None
        self._vel: np.ndarray = None
        self._target: np.ndarray = None
        self._step_vector: np.ndarray = None
        self.obstacles: list[Obstacle] = []
        self._field_limits: list[Tuple[float, float]] = []
        # self._rejected_paths: list[Tuple[Tuple[float, float], float]] = []
        self._best_rejected_path: Tuple[Tuple[float, float], float] = None


    def find_path(self, pos: Tuple[float, float], target: Tuple[float, float]):
        self._pos = np.array(pos)
        self._target = np.array(target)
        self._step_vector = self._target - self._pos
        
        next_point, collision_time = self._validate_path(self._pos, self._step_vector)

        if collision_time is None:
            return next_point
        else:
            # self._rejected_paths.append((next_point, collision_time))
            self._best_rejected_path = (next_point, collision_time)

        sub_destinations = self._gen_rnd_subdests()

        for sub_dest in sub_destinations:
            next_point, collision_time = self._validate_path(self._pos, sub_dest)

            if collision_time is None:
                return next_point
            else:
                if collision_time > self._best_rejected_path[1]:
                    self._best_rejected_path = (next_point, collision_time)


    def _validate_path(self):
        ...


    def set_field_limits(self, limits: list[Tuple[float, float]]):
        self._field_limits = limits


    def _gen_rnd_subdests(self):
        ...

