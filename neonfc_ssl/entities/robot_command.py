from dataclasses import dataclass
from typing import Tuple, Optional
from math import sqrt, sin, cos

from neonfc_ssl.entities.robot import OmniRobot


@dataclass
class RobotCommand:
    # General
    robot: OmniRobot

    # Decision
    target_pose: Optional[Tuple[float, float, float]] = None  # x, y, theta
    kick_speed: Tuple[float, float] = (0, 0)  # vx, vz
    spinner: bool = False

    # Control
    move_speed: Optional[Tuple[float, float, float]] = None  # vx, vy, omega
    local_speed: Optional[Tuple[float, float, float]] = None
    wheel_speed: Optional[Tuple[float, float, float, float]] = None

    def limit_speed(self, v):
        if (speed := sqrt(self.move_speed[0]**2 + self.move_speed[1]**2)) > v:
            ratio = v/speed

            self.move_speed = (self.move_speed[0]*ratio, self.move_speed[1]*ratio, self.move_speed[2])

    def global_speed_to_wheel_speed(self):
        vx, vy, w = self.move_speed

        R = self.robot.dimensions['L']
        r = self.robot.dimensions['R']
        theta = self.robot.theta

        a = 0.7071 #1/raiz2
        st = sin(theta)
        ct = cos(theta)

        w1 = (-R * w + a * vx * (ct - st) + a * vy * (ct + st)) / r
        w2 = (-R * w + a * vx * (-ct - st) + a * vy * (ct - st)) / r
        w3 = (-R * w + a * vx * (-ct + st) + a * vy * (-ct - st)) / r
        w4 = (-R * w + a * vx * (ct + st) + a * vy * (-ct + st)) / r

        self.wheel_speed = (w2, w3, w4, w1)
