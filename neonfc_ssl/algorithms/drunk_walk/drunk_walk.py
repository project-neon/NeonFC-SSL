from typing import Tuple


def line_line_intersection(start_l1, end_l1, start_l2, end_l2):
    ...


def line_circle_intersection(start, end, center, radius):
    ...


def line_rect_intersection(start, end, v1, v2, v3, v4):
    ...


'''
1. Generate obstacles that can be either static or dynamic ones.
requirements:
    obstacle dataclasses: dynamic obstacle and static obstacle
        Obstacle: has check_for_collision method, receive line segment and return the time of the first collision
        Static obstacle: will be considered a rectangle, so its vertices will be stored. Collision checking will be simpler
        Dynamic obstacle: will be considered a circle, so its center and radius will be stored along with its speed.
            Collision check will take into consideration 

2. Adapt the input to fit the algorithm. There are 2 cases that needs attention:
    - If the target point overlaps with an obstacle, move it to the closest point outside the obstacle.
    - If the robot position overlaps with an obstacle, just remove the obstacle from the list.

3. Find a path. 
By either going directly to the target, if possible, or by generating random subdestinations. As the algorithm proposes.
Sometimes it is not possible to find an optimal path, in those cases, return the rejected path with the highest collision time.

4. Execute the trajectory, adapting it for the control we have, instead of returning the full path,
it will return a point of the chosen trajectory with fixed distance.
'''

class DrunkWalk:
    def __init__(self) -> None:
        self.pos: Tuple[float, float, float] = None
        self.vel: Tuple[float, float] = None
        self.dest: Tuple[float, float] = None
        self.obstacles: list[Tuple[float, float]] = None    


    def _gen_rnd_subdests(self):
        ...


    def _check_for_collision(self, pos, dest):
        ...
