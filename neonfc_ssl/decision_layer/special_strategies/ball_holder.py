import math
import numpy as np
from neonfc_ssl.decision_layer.skills import *
from neonfc_ssl.decision_layer.special_strategies.special_strategy import SpecialStrategy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData
    from ..skills.base_skill import BaseSkill

def angle_between(p1, p2, p3):
    return math.atan2(p3[1] - p1[1], p3[0] - p1[0]) - math.atan2(p2[1] - p1[1], p2[0] - p1[0])


class BallHolder(SpecialStrategy):
    def __init__(self):
        super().__init__()
        self.passable_robots = []
        self.intercepting_robots = []

        self._shooting_value = 0
        self._pass_value = 0
        self._pass_target = np.array([0, 0])

        self.p = None
        self.val_max = None
        self.vals = None

        self.states: dict[str, 'BaseSkill'] = {
            'pass': SimplePass(),
            'go_to_ball': GoToBall(),
            'wait': Wait(),
            'shoot': Shoot(),
            'dribble': Dribble()
        }

        def close_to_ball(data: "MatchData"):
            robot = data.robots[self._robot_id]
            ball = data.ball

            return (((robot.x - ball.x) ** 2 + (robot.y - ball.y) ** 2) ** .5) < 0.12

        def not_func(f):
            def wrapped(*args, **kwargs):
                return not f(*args, **kwargs)

            return wrapped

        def wrapped_stop_pass(data: "MatchData"):
            robot = data.robots[self._robot_id]
            ball = data.ball

            return SimplePass.stop_pass(robot=robot, ball=ball)

        self.states['pass'].add_transition(self.states['go_to_ball'], wrapped_stop_pass)
        self.states['wait'].add_transition(self.states['go_to_ball'], not_func(close_to_ball))
        self.states['shoot'].add_transition(self.states['go_to_ball'], not_func(close_to_ball))
        self.states['dribble'].add_transition(self.states['wait'], not_func(close_to_ball))
        self.states['go_to_ball'].add_transition(self.states['wait'], close_to_ball)
        self.states['dribble'].add_transition(self.states['pass'], self.pass_transition)
        self.states['dribble'].add_transition(self.states['shoot'], self.shoot_transition)
        self.states['wait'].add_transition(self.states['pass'], self.pass_transition)
        self.states['wait'].add_transition(self.states['shoot'], self.shoot_transition)
        self.states['wait'].add_transition(self.states['dribble'], self.dribble_transition)

        self.message = None
        self.passing_to = None

    def _start(self):
        self.active = self.states['go_to_ball']
        self.active.start(self._robot_id)

    def decide(self, data):
        self.passable_robots = [r for r in data.robots if not r.missing and r.id != self._robot_id]
        self.intercepting_robots = [r for r in data.opposites if not r.missing]

        self.update_shooting_value(data)
        self.update_pass_value(data)

        next = self.active.update(data)
        if next != self.active:
            self.active = next
            if self.active.name == "Pass":
                self.active.start(self._robot_id, target=self._pass_target)
            elif self.active.name == "Dribble":
                self.active.start(self._robot_id, target=self._pass_target)
            else:
                self.active.start(self._robot_id)

        return self.active.decide(data)

    def update_shooting_value(self, data: "MatchData"):
        robot = data.robots[self._robot_id]

        if robot.x > 9:
            self._shooting_value = 0
            return

        robot_lock = (robot.x, 0)

        goal_posts = ((9, 2.5), (9, 3.5))
        goal_posts = (
            angle_between(robot, robot_lock, goal_posts[0]), angle_between(robot, robot_lock, goal_posts[1])
        )

        robot_angles = [angle_between(robot, robot_lock, robot)
                        for op in data.opposites if op.x > robot.x and not op.missing]
        robot_angles.append(goal_posts[0])
        robot_angles.append(goal_posts[1])

        robot_angles.sort()
        robot_angles = list(filter(lambda x: goal_posts[0] <= x <= goal_posts[1], robot_angles))

        diffs = []

        for a, b in zip(robot_angles[:-1], robot_angles[1:]):
            diffs.append((a, b - a))

        _, window = max(diffs, key=lambda x: x[1])

        self._shooting_value = 5 * window / math.pi

    def update_pass_value(self, data: "MatchData"):
        p = self._passing_targets()
        vals = self._receiving_probability(p, data) * self._pass_probability(p, data) * self._goal_probability(p, data)
        target = np.argmax(vals)

        self._pass_value = vals[target]
        self._pass_target = p[target]

    def dribble_transition(self, data: "MatchData"):
        # if self._shooting_value < self._pass_value:
        #     return True
        if self._shooting_value < self._pass_value and \
                np.sum(np.square(data.possession.contact_start_position-self._pass_target)) < 0.9:
            return True

        return False

    def pass_transition(self, data: "MatchData"):
        # return False
        if self._shooting_value < self._pass_value and \
                np.sum(np.square(data.possession.contact_start_position-self._pass_target)) >= 0.9:
            return True

        return False

    def shoot_transition(self, data: "MatchData"):
        if self._shooting_value >= self._pass_value:
            return True

        return False

    def _pass_probability(self, p, data):
        robot = data.robots[self._robot_id]

        dp = p - robot
        px = dp[:, 0]
        py = dp[:, 1]

        norm = px * px + py * py
        total = np.inf*np.ones(p.shape[0])

        for op in self.intercepting_robots:
            u = np.divide((op[0] - robot[0]) * px + (op[1] - robot[1]) * py, norm)
            u = np.minimum(np.maximum(u, 0), 1)

            dx = robot[0] + u * px - op[0]
            dy = robot[1] + u * py - op[1]

            total = np.minimum(dx**2 + dy**2, total)

        # return total
        return np.minimum(np.sqrt(total), 1)

    def _receiving_probability(self, p, data):
        closest_teammate_dist = np.inf * np.ones(p.shape[0])
        for r in self.passable_robots:
            closest_teammate_dist = np.minimum(np.sum(np.square(r-p), axis=1), closest_teammate_dist)

        closest_opponent_dist = np.inf * np.ones(p.shape[0])
        for r in self.intercepting_robots:
            closest_opponent_dist = np.minimum(np.sum(np.square(r-p), axis=1), closest_opponent_dist)

        return closest_opponent_dist > closest_teammate_dist

    def _goal_probability(self, p, data):
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

    @staticmethod
    def _passing_targets():
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
