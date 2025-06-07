import time
import numpy as np
from numpy.linalg import norm
from ..tracking_data import TrackedBall

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
            vz=0,
            v_shoot=np.array((0, 0))
        )

    def get_speed(self):
        return self.data.speed

    def update(self, b: 'InputBall', field: 'Geometry'):
        # TODO: encapsulate all this inside an update function the dataclass
        last_speed = self.get_speed()
        self.data.x = b.x + field.field_length/2
        self.data.y = b.y + field.field_width/2
        self.data.z = b.z
        self.data.vx = b.vx
        self.data.vy = b.vy
        self.data.vz = b.vz

        self.data.update_speed()

        if self.data.speed > last_speed + 0.01:
            self.data.update_v_shoot()

    def __getitem__(self, item):
        return self.data[item]

    def __getattr__(self, item):
        return self.data.__getattribute__(item)

    def __array__(self, dtype=None, copy=None):
        if copy is False:
            raise ValueError("`copy=False` isn't supported")
        return np.array([self.x, self.y], dtype=dtype)
