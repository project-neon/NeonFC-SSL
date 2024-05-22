from dataclasses import dataclass
from typing import Tuple
from math import sqrt


@dataclass
class RobotCommand:
    robot_id: int
    move_speed: Tuple[float, float, float] = (0, 0, 0)  # vx, vy, theta
    wheel_speed: Tuple[float, float, float, float] = (0, 0, 0, 0)
    kick_speed: Tuple[float, float] = (0, 0)  # vx, vz
    spinner: bool = False

    def limit_speed(self, v):
        if (speed := sqrt(self.move_speed[0]**2 + self.move_speed[1]**2)) > v:
            ratio = v/speed

            self.move_speed = (self.move_speed[0]*ratio, self.move_speed[1]*ratio, self.move_speed[2])
