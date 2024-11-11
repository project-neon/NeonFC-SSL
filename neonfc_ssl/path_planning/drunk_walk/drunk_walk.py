from typing import Tuple
from neonfc_ssl.path_planning.drunk_walk.obstacle import Obstacle
from neonfc_ssl.path_planning.drunk_walk.static_obstacle import StaticObstacle
from neonfc_ssl.path_planning.drunk_walk.dynamic_obstacle import DynamicObstacle
from random import uniform, choice
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

4. Execute the trajectory.
# TODO: evaluate first if really needed i will do it.
Adapt it for the control we have, instead of returning the full path,
it will return a point of the chosen trajectory with fixed distance.
'''


class DrunkWalk:
    def __init__(self) -> None:
        self._pos: np.ndarray = None
        self._target: np.ndarray = None
        self._step_vector: np.ndarray = None
        self.obstacles: list[Obstacle] = []
        self._field_limits: list[Tuple[float, float]] = []
        self.min_angle = 0
        self._best_rejected_path: Tuple[Tuple[float, float], float] = None


    def start(self, pos: Tuple[float, float], target: Tuple[float, float]):
        self._pos = np.array(pos)
        self._target = np.array(target)
        self._step_vector = self._target - self._pos


    def find_path(self) -> Tuple[float, float]:
        self.obstacles.sort(key=lambda o: o.distance_to(self._pos))
        self.min_angle = np.arctan2( 0.09, self.obstacles[0].distance_to(self._pos) )
        
        next_point, collision_time = self._validate_path(self._step_vector)

        if collision_time is None:
            return next_point #
        else:
            self._best_rejected_path = (next_point, collision_time)

        sub_destinations = self._gen_static_subdests()

        for i, sub_dest in enumerate(sub_destinations):
            next_point, collision_time = self._validate_path(sub_dest)

            if collision_time is None:
                return next_point #
            elif collision_time > self._best_rejected_path[1]:
                self._best_rejected_path = (next_point, collision_time)

        return self._best_rejected_path[0] #


    def _validate_path(self, step_vector: np.ndarray) -> Tuple[Tuple[float, float], float]:
        current_pos: np.ndarray = None

        for t in np.arange(0.05, 1.05, 0.05):
            current_pos = self._pos + t*step_vector

            # for obs in self.obstacles:
            obs = self.obstacles[0]
            if obs.check_for_collision(current_pos, t):
                return array2tuple(current_pos), t

        return array2tuple(current_pos), None
    

    def _gen_rnd_subdests(self) -> list[np.ndarray]:
        angles = [choice((1, -1))*uniform(self.min_angle, np.pi/2) for i in range(10)]
        angles.sort(key=lambda a: abs(a))

        r = np.sqrt( self._step_vector[0]**2 + self._step_vector[1]**2 )
        theta = np.arctan2(self._step_vector[1], self._step_vector[0])

        new_thetas = [theta + a for a in angles]

        result = [np.array( r*np.cos(a), r*np.sin(a) ) for a in new_thetas]

        return result


    def _gen_static_subdests(self) -> list[np.ndarray]:
        angles = list(np.linspace(-np.pi / 2, np.pi / 2, 10))
        angles.sort(key=lambda a: abs(a))

        r = np.sqrt(self._step_vector[0] ** 2 + self._step_vector[1] ** 2)
        theta = np.arctan2(self._step_vector[1], self._step_vector[0])

        new_thetas = [theta + a for a in angles]

        result = [np.array(r * np.cos(a), r * np.sin(a)) for a in new_thetas]

        return result


    def _gen_static_subdests(self) -> list[np.ndarray]:
        angles = list(np.linspace(-np.pi/2, np.pi/2, 10))
        angles.sort(key=lambda a: abs(a))

        r = np.sqrt(self._step_vector[0] ** 2 + self._step_vector[1] ** 2)
        theta = np.arctan2(self._step_vector[1], self._step_vector[0])

        new_thetas = [theta + a for a in angles]

        result = [np.array(r * np.cos(a), r * np.sin(a)) for a in new_thetas]

        return result


    def set_field_limits(self, limits: list[Tuple[float, float]]) -> None:
        self._field_limits = limits

    
    def _add_obstacle(self, obs: Obstacle):
        # if obs.distance_to(self._pos) < 0.1:
        #     return
        
        if (dist := obs.distance_to(self._target) - 0.075) < 0:
            v = obs.get_vector(self._target)
            if (v_norm := np.linalg.norm(v)) != 0:
                self._target += dist*(v/v_norm)
        
        # if np.dot(obs.get_vector(self._pos), self._step_vector) >= 0:
        self.obstacles.append(obs)


    def add_dynamic_obstacle(self, center, radius, speed):
        self._add_obstacle(DynamicObstacle(center=center, radius=radius, speed=speed))
    

    def add_static_obstacle(self, start, length, height):
        self._add_obstacle(StaticObstacle(start=start, length=length, height=height))
