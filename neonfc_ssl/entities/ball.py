import time
from collections import deque
import copy
import numpy as np
from neonfc_ssl.algorithms.kalman_filter import KalmanFilter
import math
from neonfc_ssl.match.match_data import TrackedBall
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.input_l.input_data import Geometry, Ball as InputBall


class Ball:
    def __init__(self, match):
        self.lt = time.time()
        self.dt = 1 / 60

        self.match = match

        self.data = TrackedBall(
            x=0,
            y=0,
            z=0,
            vx=0,
            vy=0,
            vz=0
        )

    def get_speed(self):
        return (self.data.vx ** 2 + self.data.vy ** 2) ** .5

    def update(self, b: 'InputBall', field: 'Geometry'):
        self.data.x = b.x + field.field_length/2
        self.data.y = b.y + field.field_width/2
        self.data.z = b.z
        self.data.vx = b.vx
        self.data.vy = b.vy
        self.data.vz = b.vz

    def pos_after(self, dt):
        # t_max = a/v
        # pos = initial_pos + initial_v * t_target + 0.5 * a * t_target ^ 2
        a = 0.8

        t_max_x = abs(self.data.vx/a) if a else 0
        t_max_y = abs(self.data.vy/a) if a else 0

        dt_x = min(dt, t_max_x)
        dt_y = min(dt, t_max_y)

        return (self.data.x + self.data.vx * dt_x - math.copysign(0.5 * a * dt_x ** 2, self.data.vx),
                self.data.y + self.data.vy * dt_y - math.copysign(0.5 * a * dt_y ** 2, self.data.vy))

    def stopping_pos(self):
        # t_max = a/v
        # pos = initial_pos + initial_v * t_target + 0.5 * a * t_target ^ 2
        a = 0.005 * math.pi * 9.81
        a = 0.3

        t_max_x = abs(self.data.vx/a) if a else 0
        t_max_y = abs(self.data.vy/a) if a else 0

        dt_x = t_max_x
        dt_y = t_max_y

        return (self.data.x + self.data.vx * dt_x - math.copysign(0.5 * a * dt_x ** 2, self.data.vx),
                self.data.y + self.data.vy * dt_y - math.copysign(0.5 * a * dt_y ** 2, self.data.vy))

    def __getitem__(self, item):
        return self.data[item]

    def __getattr__(self, item):
        return self.data.__getattribute__(item)

    def __array__(self, dtype=None, copy=None):
        if copy is False:
            raise ValueError("`copy=False` isn't supported")
        return np.array([self.x, self.y], dtype=dtype)
