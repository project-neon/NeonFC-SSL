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
        self.kf = KalmanFilter(4, 2, 4)
        self.lt = time.time()
        self.dt = 1/60
        self._update_kalman(create=True)
        self.use_kalman = False

        self.current_data = []

        self._frames = {
            'x': deque(maxlen=10),
            'y': deque(maxlen=10)
        }

        self.vx, self.vy = 0, 0
        self.x, self.y = 0, 0
        self.lx, self.ly = 0, 0
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
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
        else:
            C = None

        self.kf.change_matrices(A, B, C)

        sig = .1
        Q = np.array([
            [sig, 0, 0, 0],
            [0, sig, 0, 0],
            [0, 0, 1.4*sig/self.dt, 0],
            [0, 0, 0, 1.4*sig/self.dt]
        ])

        self.kf.change_covariance(Q=Q)

    def get_name(self):
        return 'BALL'

    def get_speed(self):
        return (self.vx**2 + self.vy**2)**.5

    def update(self, frame, field):
        self.current_data = frame.get('ball')
        if self.current_data is not None:
            self._update_speeds(field)

    def pos_after(self, dt):
        # t_max = a/v
        # pos = initial_pos + initial_v * t_target + 0.5 * a * t_target ^ 2
        a = 0.8

        t_max_x = abs(self.vx/a) if a else 0
        t_max_y = abs(self.vy/a) if a else 0

        dt_x = min(dt, t_max_x)
        dt_y = min(dt, t_max_y)

        return (self.x + self.vx * dt_x - math.copysign(0.5 * a * dt_x ** 2, self.vx),
                self.y + self.vy * dt_y - math.copysign(0.5 * a * dt_y ** 2, self.vy))

    def stopping_pos(self):
        # t_max = a/v
        # pos = initial_pos + initial_v * t_target + 0.5 * a * t_target ^ 2
        a = 0.005 * math.pi * 9.81
        a = 0.3

        t_max_x = abs(self.vx/a) if a else 0
        t_max_y = abs(self.vy/a) if a else 0

        dt_x = t_max_x
        dt_y = t_max_y

        return (self.x + self.vx * dt_x - math.copysign(0.5 * a * dt_x ** 2, self.vx),
                self.y + self.vy * dt_y - math.copysign(0.5 * a * dt_y ** 2, self.vy))

    def _update_speeds(self, field):
        if self.use_kalman:
            self._update_kalman()
            u = np.array([
                [0],
                [0]
            ])

            vx = (self.current_data['x'] - self.lx)/self.dt
            vy = (self.current_data['y'] - self.ly)/self.dt
            self.lx, self.ly = self.current_data['x'], self.current_data['y']

            z = np.array([
                [self.current_data['x']],
                [self.current_data['y']],
                [vx],
                [vy]
            ])

            kf_output = self.kf(u, z)

            self._np_array = kf_output

            self.x = kf_output[0, 0]
            self.y = kf_output[1, 0]
            self.vx = kf_output[2, 0]
            self.vy = kf_output[3, 0]

        else:
            self.x = self.current_data['x'] + 0.5 * field.fieldLength
            self.y = self.current_data['y'] + 0.5 * field.fieldWidth
            self.vx = self.current_data['vx']
            self.vy = self.current_data['vy']

    def __getitem__(self, item):
        if item == 0:
            return self.x

        if item == 1:
            return self.y

        raise IndexError("Ball only has 2 coordinates")

    def __array__(self, dtype=None, copy=None):
        if copy is False:
            raise ValueError("`copy=False` isn't supported")
        if self.use_kalman:
            return self._np_array[:2, 0].astype(dtype)
        return np.array([self.x, self.y], dtype=dtype)
