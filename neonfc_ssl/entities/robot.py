import math
import time
from collections import deque
from math import sin, cos, pi
import numpy as np
from neonfc_ssl.algorithms.kalman_filter import KalmanFilter
from neonfc_ssl.commons.math import reduce_ang, distance_between_points


class OmniRobot:
    def __init__(self, match, team_color, robot_id) -> None:
        self.kf = KalmanFilter(6, 3, 3)
        self.lt = time.time()
        self.dt = 1 / 60
        self._update_kalman(create=True)

        self.match = match
        self.robot_id = robot_id
        self.team_color = team_color

        self.strategy = None

        self.dimensions = {
            'L': 0.075,
            'R': 0.035
        }

        self.last_poses = {
            'x': deque(maxlen=10),
            'y': deque(maxlen=10),
            'theta': deque(maxlen=10)
        }

        self.vx, self.vy, self.vtheta = 0, 0, 0
        self.x, self.y, self.theta = 0, 0, 0

        self.speed = 0
        self.last_appearance = -1
        self.missed_frames = 0
        self.missing = True
        self.ALLOWED_MISSING_FRAMES = 20  # in seconds

        self.current_data = None
        self.strategy = None
        self._np_array = None

    def get_name(self):
        return 'SSLROBOT_{}_{}'.format(self.robot_id, self.team_color)

    def set_strategy(self, strategy_ref):
        if self.strategy != strategy_ref:
            self.strategy = strategy_ref
            self.strategy.start(self)

    def get_robot_in_frame(self, frame):
        team_color_key = 'robotsBlue' if self.team_color == 'blue' else 'robotsYellow'

        if frame.get(team_color_key) is None:
            return None
        robot_data = frame[team_color_key].get(self.robot_id)
        return robot_data

    def _update_kalman(self, create=False):
        t = time.time()
        self.dt = t - self.lt
        self.lt = t

        A = np.array([
            [1, 0, 0, self.dt, 0, 0],
            [0, 1, 0, 0, self.dt, 0],
            [0, 0, 1, 0, 0, self.dt],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ])

        B = np.array([
            [.5 * self.dt ** 2, 0, 0],
            [0, .5 * self.dt ** 2, 0],
            [0, 0, .5 * self.dt ** 2],
            [self.dt, 0, 0],
            [0, self.dt, 0],
            [0, 0, self.dt]
        ])

        if create:
            C = np.array([
                [1, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0]
            ])
        else:
            C = None

        self.kf.change_matrices(A, B, C)

    def get_speed(self):
        return (self.vx ** 2 + self.vy ** 2) ** .5

    def update_pose(self):
        self._update_kalman()
        u = np.array([
            [0],
            [0],
            [0]
        ])
        z = np.array([
            [self.current_data['x']],
            [self.current_data['y']],
            [self.current_data['theta']]
        ])

        kf_output = self.kf(u, z)

        self._np_array = kf_output

        self.x = kf_output[0, 0]
        self.y = kf_output[1, 0]
        self.theta = reduce_ang(kf_output[2, 0])
        self.vx = kf_output[3, 0]
        self.vy = kf_output[4, 0]
        self.vtheta = kf_output[5, 0]

    def update(self, frame):
        self.current_data = self.get_robot_in_frame(frame)
        if self.current_data.get('tCapture') != self.last_appearance:
            self.last_appearance = self.current_data.get('tCapture')
            self.missing = False
            self.missed_frames = 0
            self.update_pose()
        else:
            self.missed_frames += 1
            self.missing = self.missed_frames >= self.ALLOWED_MISSING_FRAMES if not self.missing else True

    def decide(self):
        desired = self.strategy.decide()
        desired.wheel_speed = self.global_speed_to_wheel_speed(*desired.move_speed)
        return desired

    def global_speed_to_wheel_speed(self, vx, vy, w):
        R = self.dimensions['L']
        r = self.dimensions['R']
        theta = self.theta

        a = 0.7071
        st = sin(theta)
        ct = cos(theta)

        w1 = (-R * w + a * vx * (ct - st) + a * vy * (ct + st)) / r
        w2 = (-R * w + a * vx * (-ct - st) + a * vy * (ct - st)) / r
        w3 = (-R * w + a * vx * (-ct + st) + a * vy * (-ct - st)) / r
        w4 = (-R * w + a * vx * (ct + st) + a * vy * (-ct + st)) / r

        return w2, w3, w4, w1

    def time_to_ball(self, ball):
        avg_speed = .5
        pos = np.array(ball)
        last_t = 0
        for _ in range(50):
            t = distance_between_points(pos, self)/avg_speed
            pos = ball.pos_after(t)

            if abs(t - last_t) < 0.01:
                return t

            last_t = t
        return last_t

    def __repr__(self):
        return f"{self.team_color} Robot {self.robot_id} ({self.x:.2f}, {self.y:.2f}, {self.theta:.2f})"

    def __getitem__(self, item):
        if item == 0:
            return self.x

        if item == 1:
            return self.y

        if item == 2:
            return self.theta

        raise IndexError("Robot only has 3 coordinates")

    def __array__(self, dtype=None, copy=None):
        if copy is False:
            raise ValueError("`copy=False` isn't supported")
        return self._np_array[:2, 0].astype(dtype)
