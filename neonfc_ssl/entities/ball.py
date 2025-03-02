import time
from collections import deque
import copy
import numpy as np
from neonfc_ssl.algorithms.kalman_filter import KalmanFilter
import math
from neonfc_ssl.match.match_data import TrackedBall
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.input_layer.input_data import Geometry, Ball as InputBall


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


    def __getitem__(self, item):
        return self.data[item]

    def __getattr__(self, item):
        return self.data.__getattribute__(item)

    def __array__(self, dtype=None, copy=None):
        if copy is False:
            raise ValueError("`copy=False` isn't supported")
        return np.array([self.x, self.y], dtype=dtype)
