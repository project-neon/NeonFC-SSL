from neonfc_ssl.skills import *
from neonfc_ssl.strategies.base_strategy import BaseStrategy
import math
import numpy as np
import time
from collections import deque
import socket


def angle_between(p1, p2, p3):
    return math.atan2(p3[1] - p1[1], p3[0] - p1[0]) - math.atan2(p2[1] - p1[1], p2[0] - p1[0])


class BallHolder(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Ball Holder', coach, match)
        self.passable_robots = []
        self.intercepting_robots = []

        self.t0 = time.time()
        self.last_info = time.time()
        self.ts = deque(maxlen=60)

        self._shooting_value = 0
        self._pass_value = 0
        self._pass_target = np.array([0, 0])

        self.p = None
        self.val_max = None
        self.vals = None

        self.states = {
            'pass': SimplePass(coach, match),
            'go_to_ball': GoToBall(coach, match),
            'wait': Wait(coach, match),
            'shoot': Shoot(coach, match),
            'dribble': Dribble(coach, match),
            'wait_outside_area': MoveToPose(coach, match)
        }

        def close_to_ball():
            return (((self._robot.x - self._match.ball.x) ** 2 + (self._robot.y - self._match.ball.y) ** 2) ** .5) < 0.12

        def not_func(f):
            def wrapped():
                return not f()

            return wrapped

        def and_func(f1, f2):
            def wrapped():
                return f1() and f2()

            return wrapped

        def wrapped_stop_pass():
            return SimplePass.stop_pass(robot=self._robot, ball=self._match.ball)

        self.states['pass'].add_transition(self.states['go_to_ball'], and_func(wrapped_stop_pass, not_func(self.ball_inside_area)))
        self.states['wait'].add_transition(self.states['go_to_ball'], and_func(not_func(close_to_ball), not_func(self.ball_inside_area)))
        self.states['shoot'].add_transition(self.states['go_to_ball'], and_func(not_func(close_to_ball), not_func(self.ball_inside_area)))
        self.states['dribble'].add_transition(self.states['wait'], not_func(close_to_ball))
        self.states['go_to_ball'].add_transition(self.states['wait'], close_to_ball)
        self.states['dribble'].add_transition(self.states['pass'], self.pass_transition)
        self.states['dribble'].add_transition(self.states['shoot'], self.shoot_transition)
        self.states['wait'].add_transition(self.states['pass'], and_func(self.pass_transition, not_func(self.ball_inside_area)))
        self.states['wait'].add_transition(self.states['shoot'], and_func(self.shoot_transition, not_func(self.ball_inside_area)))
        self.states['wait'].add_transition(self.states['dribble'], and_func(self.dribble_transition, not_func(self.ball_inside_area)))
        self.states['go_to_ball'].add_transition(self.states['wait_outside_area'], self.ball_inside_area)
        self.states['pass'].add_transition(self.states['wait_outside_area'], self.ball_inside_area)
        self.states['shoot'].add_transition(self.states['wait_outside_area'], self.ball_inside_area)
        self.states['dribble'].add_transition(self.states['wait_outside_area'], self.ball_inside_area)
        self.states['wait'].add_transition(self.states['wait_outside_area'], self.ball_inside_area)
        self.states['wait_outside_area'].add_transition(self.states['wait'], not_func(self.ball_inside_area))

        self.message = None
        self.passing_to = None

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 5005

    def _start(self):
        self.active = self.states['go_to_ball']
        self.active.start(self._robot)

    def decide(self):
        self.passable_robots = [r for r in self._match.robots if not r.missing and r is not self._robot]
        self.intercepting_robots = [r for r in self._match.opposites if not r.missing]
        
        self.update_shooting_value()
        self.update_pass_value()

        next = self.active.update()
        if next != self.active:
            self.active = next
            if self.active.name == "Pass":
                self.active.start(self._robot, target=self._pass_target)
            elif self.active.name == "Dribble":
                self.active.start(self._robot, target=self._pass_target)
            elif self.active.name == "MoveToPose":
                self.active.start(self._robot, target=[self._match.field.fieldLength/2, self._match.field.fieldWidth/2, 0])
            else:
                self.active.start(self._robot)

        if time.time() - self.last_info > 0.1:
            self.last_info = time.time()
            MESSAGE = 'a'.join([
                ';'.join([f"%0.2f,%0.2f" % (r.x, r.y) for r in self.passable_robots]),
                ';'.join([f"%0.2f,%0.2f" % (r.x, r.y) for r in self.intercepting_robots]),
                "%0.2f,%0.2f" % (self._robot.x, self._robot.y)
            ]).encode('ascii')
            self.sock.sendto(MESSAGE, (self.UDP_IP, self.UDP_PORT))

        com = self.active.decide()
        com.ignore_friendly_robots = False
        return com

    def update_shooting_value(self):
        if self._robot.x > 9:
            self._shooting_value = 0
            return

        robot_lock = (self._robot.x, 0)

        goal_posts = ((9, 2.5), (9, 3.5))
        goal_posts = (
            angle_between(self._robot, robot_lock, goal_posts[0]), angle_between(self._robot, robot_lock, goal_posts[1])
        )

        robot_angles = [angle_between(self._robot, robot_lock, robot)
                        for robot in self._match.opposites if robot.x > self._robot.x and not robot.missing]
        robot_angles.append(goal_posts[0])
        robot_angles.append(goal_posts[1])

        robot_angles.sort()
        robot_angles = list(filter(lambda x: goal_posts[0] <= x <= goal_posts[1], robot_angles))

        diffs = []

        for a, b in zip(robot_angles[:-1], robot_angles[1:]):
            diffs.append((a, b - a))

        _, window = max(diffs, key=lambda x: x[1])

        self._shooting_value = 5 * window / math.pi

    def update_pass_value(self):
        p = self._passing_targets()
        vals = 1 * self._receiving_probability(p) * self._pass_probability(p) * self._goal_probability(p)
        target = np.argmax(vals)

        self._pass_value = vals[target]
        self._pass_target = p[target]
    
    def dribble_transition(self):
        # if self._shooting_value < self._pass_value:
        #     return True
        if self._shooting_value < self._pass_value and \
                np.sum(np.square(self._match.possession.contact_start_position-self._pass_target)) < 0.9:
            return True

        return False

    def pass_transition(self):
        # return False
        if self._shooting_value < self._pass_value and \
                np.sum(np.square(self._match.possession.contact_start_position-self._pass_target)) >= 0.9:
            return True

        return False

    def ball_inside_area(self):
        f = self._match.field
        b = self._match.ball
        return (b.x <= f.penaltyAreaDepth and
                (f.penaltyAreaWidth - f.fieldWidth)/2 <= b.y <= (f.penaltyAreaWidth + f.fieldWidth)/2)

    def shoot_transition(self):
        if self._shooting_value >= self._pass_value:
            return True

        return False

    def _passing_targets(self):
        return self._close_targets()

    def _close_targets(self):
        dx, dy = 0.1, 0.1

        r = .7
        lwx, upx = min(self._robot.x + r, self._match.field.fieldLength), max(self._robot.x - r, 0)
        lwy, upy = min(self._robot.y + r, self._match.field.fieldWidth), max(self._robot.y - r, 0)

        x = np.linspace(lwx + dx, upx - dx, 10)
        y = np.linspace(lwy + dy, upy - dy, 10)
        xs, ys = np.meshgrid(x, y)

        return np.transpose(np.array([xs.flatten(), ys.flatten()]))

    def _attack_targets(self):
        dx, dy = 0.1, 0.1

        # Area 0
        lwx, upx = 4.5, 9
        lwy, upy = 0, 2

        x = np.linspace(lwx+dx, upx-dx, 18)
        y = np.linspace(lwy+dy, upy-dy, 8)
        xs, ys = np.meshgrid(x, y)
        a0 = np.transpose(np.array([xs.flatten(), ys.flatten()]))

        # Area 1
        lwx, upx = 4.5, 8
        lwy, upy = 2, 4

        x = np.linspace(lwx+dx, upx-dx, 14)
        y = np.linspace(lwy+dy, upy-dy, 10)
        xs, ys = np.meshgrid(x, y)
        a1 = np.transpose(np.array([xs.flatten(), ys.flatten()]))

        # Area 2
        lwx, upx = 4.5, 9
        lwy, upy = 4, 6

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
