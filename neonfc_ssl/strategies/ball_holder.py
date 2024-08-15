from neonfc_ssl.skills import *
from neonfc_ssl.strategies.base_strategy import BaseStrategy
import math
import numpy as np
import time
from collections import deque


def angle_between(p1, p2, p3):
    return math.atan2(p3[1] - p1[1], p3[0] - p1[0]) - math.atan2(p2[1] - p1[1], p2[0] - p1[0])


class BallHolder(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Ball Holder', coach, match)
        self.passable_robots = []
        self.intercepting_robots = []

        self.max_value = 0
        self.max_idx = 0

        self.t0 = time.time()
        self.ts = deque(maxlen=60)

        self.goal_v = 0

        self.states = {
            'pass': SimplePass(coach, match),
            'go_to_ball': GoToBall(coach, match),
            'wait': Wait(coach, match),
            'shoot': Shoot(coach, match),
        }

        def close_to_ball():
            return (((self._robot.x - self._match.ball.x) ** 2 + (self._robot.y - self._match.ball.y) ** 2) ** .5) < 0.12

        def not_func(f):
            def wrapped():
                return not f()

            return wrapped

        self.states['pass'].add_transition(self.states['go_to_ball'], not_func(close_to_ball))
        self.states['wait'].add_transition(self.states['go_to_ball'], not_func(close_to_ball))
        self.states['shoot'].add_transition(self.states['go_to_ball'], not_func(close_to_ball))
        self.states['go_to_ball'].add_transition(self.states['wait'], close_to_ball)
        self.states['wait'].add_transition(self.states['pass'], self.pass_transition)
        self.states['wait'].add_transition(self.states['shoot'], self.shoot_transition)

        self.message = None
        self.passing_to = None

    def _start(self):
        self.active = self.states['go_to_ball']
        self.active.start(self._robot)

    def decide(self):
        self.passable_robots = [r for r in self._match.robots if not r.missing and r is not self._robot]
        self.intercepting_robots = [r for r in self._match.opposites if not r.missing]

        next = self.active.update()
        if next != self.active:
            self.active = next
            if self.active.name == "Pass":
                self.passing_to = self.decide_action()
                self.active.start(self._robot, target=self.passing_to)
            else:
                self.active.start(self._robot)

        return self.active.decide()

    def decide_action(self):
        p = self._passing_targets()
        vals = self._receiving_probability(p)*self._pass_probability(p)*self._goal_probability(p)
        target = np.argmax(vals)
        return p[target]

    def pass_transition(self):
        # if self.max_value > (
        #         1 - (distance_between_points(self._robot, (9, 3)) / 9.5)) * 0.1 and self.max_value > self.goal_v:
        # if self.max_value > self.current_v:
        return True
        # return False

    def shoot_transition(self):
        # if self.goal_v > (
        #         1 - (distance_between_points(self._robot, (9, 3)) / 9.5)) * 0.1 and self.goal_v > self.max_value:
        # if self.goal_v > self.current_v and self.goal_v > self.max_value:
        #     return True
        return False

    def _passing_targets(self):
        dx, dy = 0.1, 0.1
        # Area 0
        upx, lwx = 4.5, 9
        upy, lwy = 0, 2

        x = np.linspace(lwx+dx, upx-dx, 18)
        y = np.linspace(lwy+dy, upy-dy, 8)
        xs, ys = np.meshgrid(x, y)
        a0 = np.transpose(np.array([xs.flatten(), ys.flatten()]))

        # Area 1
        upx, lwx = 4.5, 8
        upy, lwy = 2, 4

        x = np.linspace(lwx+dx, upx-dx, 14)
        y = np.linspace(lwy+dy, upy-dy, 10)
        xs, ys = np.meshgrid(x, y)
        a1 = np.transpose(np.array([xs.flatten(), ys.flatten()]))

        # Area 2
        upx, lwx = 4.5, 9
        upy, lwy = 4, 6

        x = np.linspace(lwx+dx, upx-dx, 18)
        y = np.linspace(lwy+dy, upy-dy, 8)
        xs, ys = np.meshgrid(x, y)
        a2 = np.transpose(np.array([xs.flatten(), ys.flatten()]))

        return np.concatenate((a0, a1, a2))

    def _pass_probability(self, p):
        dp = p - self._robot
        px = dp[:, 0]
        py = dp[:, 1]

        norm = px * px + py * py
        total = np.inf*np.ones(p.shape[0])

        for op in self.intercepting_robots:
            u = np.divide((op[0] - self._robot[0]) * px + (op[1] - self._robot[1]) * py, norm)
            u = np.minimum(np.maximum(u, 0), 1)

            dx = self._robot[0] + u * px - op[0]
            dy = self._robot[1] + u * py - op[1]

            total = np.minimum(dx**2 + dy**2, total)

        # return total
        return np.minimum(np.sqrt(total), 1)

    def _receiving_probability(self, p):
        closest_teammate_dist = np.inf * np.ones(p.shape[0])
        for r in self.passable_robots:
            closest_teammate_dist = np.minimum(np.sum(np.square(r-p), axis=1), closest_teammate_dist)

        closest_opponent_dist = np.inf * np.ones(p.shape[0])
        for r in self.intercepting_robots:
            closest_opponent_dist = np.minimum(np.sum(np.square(r-p), axis=1), closest_opponent_dist)

        return closest_opponent_dist > closest_teammate_dist

    def _goal_probability(self, p):
        dp = np.array([9, 3]) - p
        px = dp[:, 0]
        py = dp[:, 1]

        norm = px * px + py * py
        total = np.inf*np.ones(p.shape[0])

        for op in self.intercepting_robots:
            u = np.divide((op[0] - p[:, 0]) * px + (op[1] - p[:, 1]) * py, norm)
            u = np.minimum(np.maximum(u, 0), 1)

            dx = p[:, 0] + u * px - op[0]
            dy = p[:, 1] + u * py - op[1]

            total = np.minimum(dx**2 + dy**2, total)

        # return total
        return np.minimum(np.sqrt(total), 1)
