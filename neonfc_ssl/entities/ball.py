import time
from collections import deque
import copy
import numpy as np
from neonfc_ssl.algorithms.kalman_filter import KalmanFilter


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

    def _update_kalman(self, create=False):
        self.dt = self.lt - time.time()
        self.lt = time.time()

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