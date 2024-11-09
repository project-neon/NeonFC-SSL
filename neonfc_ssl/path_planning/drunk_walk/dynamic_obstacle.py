from neonfc_ssl.path_planning.drunk_walk.obstacle import Obstacle
from dataclasses import dataclass, field
import numpy as np


# Dynamic obstacle: will be considered a circle, so its center and radius will be stored along with its speed.
#    Collision check will take into consideration 
@dataclass
class DynamicObstacle(Obstacle):
    center: np.ndarray = field(init=True)
    radius: float
    speed: np.ndarray = field(init=True)


    def __post_init__(self):
        self.x, self.y = self.center[0], self.center[1]
        self.vx, self.vy = self.speed[0], self.speed[1]


    def get_vector(self, origin: np.ndarray) -> np.ndarray:
        return self.center - origin
    

    def distance_to(self, point: np.ndarray) -> float:
        return self.distance(self.center, point)
    

    def distance(self, origin: np.ndarray, dest: np.ndarray) -> float:
        return np.sqrt( ( origin[0] - dest[0] )**2 + ( origin[1] - dest[1] )**2 )


    def check_for_collision(self, point: np.ndarray, time_step: float) -> bool:
        # r_dyn = self.get_extra_margin(time_step)

        # the 2/3 here ended up also being a tunable parameter, dont ask why, please.
        # I will explain anyway, this is due to the f_minus modelage being f_minus=0, 
        # if it was kept with the original formula c+(v/|v|)(f_minus+r_dyn), 
        # the tail of the virtual obstacle would be always the same, to avoid that this correction move the virtual obstacle a little .
        # pos_dyn = self.center + (self.speed/np.linalg.norm(self.speed))*((2/3)*r_dyn) if np.linalg.norm(self.speed) != 0 else self.center

        return self.distance_to(point) < self.radius


    def get_extra_margin(self, time_step: float) -> float:
        future_pos = self.center + time_step*self.speed
        f_plus = self.distance_to(future_pos)

        # apparently this 2 below the f_plus can be a tunable parameter, 
        # the bigger it is the smaller the virtual obstacle projection becomes, 
        # this is different from it should be: r_dyn = (f_plus-f_minus)/2
        r_dyn = f_plus/2
        
        return r_dyn
