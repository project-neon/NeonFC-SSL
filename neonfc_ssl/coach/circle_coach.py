from neonfc_ssl.coach import HungarianCoach
from neonfc_ssl.commons.math import distance_between_points
from neonfc_ssl.strategies import Receiver, BallHolder, Test, GoalKeeper, Passer, Libero, RightBack, LeftBack
import time
import math


class Coach(HungarianCoach):
    NAME = "CircleCoach"

    def _start(self):
        self.center = (self._match.field.fieldLength/4, self._match.field.fieldWidth/2)
        self.radius = .9 * min(self._match.field.fieldWidth/4, self._match.field.fieldLength/2)
        self.turn_speed = 0.2  # rad/s
        self.start_time = time.time()
        self.settle_time = 0

    def decide(self):
        ang = 2*math.pi/self._n_active_robots
        dt = max(0, time.time() - self.start_time - self.settle_time)
        targets = [(
            self.center[0] + self.radius*math.cos(dt*self.turn_speed + i*ang),
            self.center[1] + self.radius*math.sin(dt*self.turn_speed + i*ang)
        ) for i in range(self._n_active_robots)]

        self._calculate_hungarian(self._active_robots, targets)

