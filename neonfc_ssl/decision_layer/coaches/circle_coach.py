from .base_coach import Coach
import time
import math


class Spin:
    pass


class CircleCoach(Coach):
    def _start(self):
        self.turn_speed = 0.2  # rad/s
        self.start_time = time.time()
        self.settle_time = 0

    def decide(self):
        field = self.data.field

        center = (field.field_length/4, field.field_width/2)
        radius = .9 * min(field.field_width/4, field.field_length/2)

        ang = 2*math.pi/len(self.data.robots.active)

        dt = max(0, int(time.time() - self.start_time - self.settle_time))
        targets = [((
            center[0] + radius*math.cos(dt*self.turn_speed + i*ang),
            center[1] + radius*math.sin(dt*self.turn_speed + i*ang),
        ), Spin) for i in range(len(self.data.robots.active))]

        self.decision.calculate_hungarian(
            targets=targets,
            robots=self.data.robots.active
        )
