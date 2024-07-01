import time
from collections import deque
import copy
import numpy as np
from neonfc_ssl.algorithms.kalman_filter import KalmanFilter
import math


def speed(_list, _fps):
    if len(_list) <= 1:
        return 0
    
    speed_fbf = [
        (v - i) for i, v 
        in zip(
            _list, 
            list(_list)[1:]
        )
    ]

    return _fps * (sum(speed_fbf)/len(speed_fbf))


class Ball(object):
    def __init__(self):
        self.kf = KalmanFilter(4, 2, 2)
        self.lt = time.time()
        self.dt = 1/60
        self._update_kalman(create=True)

        self.current_data = []

        self._frames = {
            'x': deque(maxlen=10),
            'y': deque(maxlen=10)
        }

        self.vx, self.vy = 0, 0
        self.x, self.y = 0, 0
        self._np_array = None

    def _update_kalman(self, create=False):
        t = time.time()
        self.dt = t - self.lt
        self.lt = t

        A = np.array([
            [1, 0, self.dt, 0],
            [0, 1, 0, self.dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])

        B = np.array([
            [.5*self.dt**2, 0],
            [0, .5*self.dt**2],
            [self.dt, 0],
            [0, self.dt]
        ])

        if create:
            C = np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
            ])
        else:
            C = None

        self.kf.change_matrices(A, B, C)

    def get_name(self):
        return 'BALL'

    def get_speed(self):
        return (self.vx**2 + self.vy**2)**.5

    def update(self, frame):
        self.current_data = frame.get('ball')
        if self.current_data is not None:
            self._update_speeds()

    def pos_after(self, dt):
        # t_max = a/v
        # pos = initial_pos + initial_v * t_target + 0.5 * a * t_target ^ 2
        a = 0.05 * math.pi * 9.81

        if self.get_speed() == 0:
            return self.x, self.y

        t_max = a/self.get_speed()
        dt = min(dt, t_max)

        return self.x + self.vx * dt + 0.5 * a * dt ** 2, self.y + self.vy * dt + 0.5 * a * dt ** 2

    def _update_speeds(self):
        self._update_kalman()
        u = np.array([
            [0],
            [0]
        ])
        z = np.array([
            [self.current_data['x']],
            [self.current_data['y']]
        ])

        kf_output = self.kf(u, z)

        self._np_array = kf_output

        self.x = kf_output[0, 0]
        self.y = kf_output[1, 0]
        self.vx = kf_output[2, 0]
        self.vy = kf_output[3, 0]

    def __getitem__(self, item):
        if item == 0:
            return self.x

        if item == 1:
            return self.y

        raise IndexError("Ball only has 2 coordinates")

    def __array__(self, dtype=None, copy=None):
        if copy is False:
            raise ValueError("`copy=False` isn't supported")
        return self._np_array[:2, 0].astype(dtype)
