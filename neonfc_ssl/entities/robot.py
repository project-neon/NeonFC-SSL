import math
import time
from collections import deque
from math import sin, cos, pi
import numpy as np
from neonfc_ssl.algorithms.kalman_filter import KalmanFilter
from neonfc_ssl.commons.math import reduce_ang, distance_between_points
from neonfc_ssl.match.match_data import TrackedRobot

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.input_l.input_data import Robot, Geometry


class OmniRobot:
    dimensions = {
        'L': 0.075,
        'R': 0.035
    }

    ALLOWED_MISSING_FRAMES = 20

    def __init__(self, match, color, robot_id, calculate_speed=False) -> None:
        self.lt = time.time()
        self.dt = 1 / 60

        self.match = match

        self.data = TrackedRobot(
            id=robot_id,
            color=color,
            x=0,
            y=0,
            theta=0,
            vx=0,
            vy=0,
            vtheta=0,
            missing=True
        )

        self.missed_frames = 0

    def get_speed(self):
        return (self.data.vx ** 2 + self.data.vy ** 2) ** .5

    def update(self, frame: dict[int, 'Robot'], field: 'Geometry'):
        r = frame.get(self.data.id)

        if r is None:
            self.missed_frames += 1
            if self.missed_frames >= self.ALLOWED_MISSING_FRAMES:
                self.data.missing = True

        else:
            self.missed_frames = 0
            self.data.missing = False

            self.data.x = r.x + field.field_length/2
            self.data.y = r.y + field.field_width/2
            self.data.theta = r.theta

            self.data.vx = r.vx
            self.data.vy = r.vy
            self.data.vtheta = r.vtheta

    def __getitem__(self, item):
        return self.data[item]

    def __getattr__(self, item):
        return self.data.__getattribute__(item)

    def __array__(self, dtype=None, copy=None):
        if copy is False:
            raise ValueError("`copy=False` isn't supported")
        return np.array([self.x, self.y], dtype=dtype)
