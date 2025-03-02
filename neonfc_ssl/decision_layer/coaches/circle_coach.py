from .base_coach import Coach
import time
import math


class CircleCoach(Coach):
    def _start(self):
        self.turn_speed = 0.2  # rad/s
        self.start_time = time.time()
        self.settle_time = 0

    def __call__(self, data):
        field = data.field

        center = (field.field_length/4, field.field_width/2)
        radius = .9 * min(field.field_width/4, field.field_length/2)

        ang = 2*math.pi/len(data.robots.active)

        dt = max(0, time.time() - self.start_time - self.settle_time)
        targets = [(
            center[0] + radius*math.cos(dt*self.turn_speed + i*ang),
            center[1] + radius*math.sin(dt*self.turn_speed + i*ang)
        ) for i in range(len(data.robots.active))]

        self.decision.calculate_hungarian(
            targets=targets,
            robots=data.robots.active
        )

