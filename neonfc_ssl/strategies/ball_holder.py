from neonfc_ssl.skills import *
from neonfc_ssl.strategies.base_strategy import BaseStrategy
import math
import numpy as np
from neonfc_ssl.commons.math import distance_between_points, angle_between_3_points


def angle_between(p1, p2, p3):
    return math.atan2(p3[1] - p1[1], p3[0] - p1[0]) - math.atan2(p2[1] - p1[1], p2[0] - p1[0])


class BallHolder(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Ball Holder', coach, match)
        self.passable_robots = []
        self.intercepting_robots = []

        self.max_value = 0
        self.max_idx = 0

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

        actions = self.pass_ex_value()

        self.max_value = max(actions)
        self.max_idx = actions.index(self.max_value)

        self.goal_v = self.goal_probability()
        self.current_v = 1 - (distance_between_points(self._robot, (9, 3)) / 9.5) - self.possession_change_probability()
        print('goal v', self.goal_v)

        next = self.active.update()

        if next != self.active:
            if self.active.name == "Pass":
                self._coach.event[self.name] = {'target', self.passing_to}
            self.active = next
            if self.active.name == "Pass":
                self.passing_to = self.passable_robots[self.max_idx]
                self.active.start(self._robot, self.passable_robots[self.max_idx])
            else:
                self.active.start(self._robot)

        return self.active.decide()

    def pass_transition(self):
        # if self.max_value > (
        #         1 - (distance_between_points(self._robot, (9, 3)) / 9.5)) * 0.1 and self.max_value > self.goal_v:
        if self.max_value > self.current_v and self.max_value > self.goal_v:
            return True
        return False

    def shoot_transition(self):
        # if self.goal_v > (
        #         1 - (distance_between_points(self._robot, (9, 3)) / 9.5)) * 0.1 and self.goal_v > self.max_value:
        if self.goal_v > self.current_v and self.goal_v > self.max_value:
            return True
        return False

    def pass_value(self):
        return [.5*(1 - (distance_between_points(r, (9, 3)) / 9.5)) for r in self.passable_robots]

    def pass_probability(self):
        # for each opponent robot closest to the ball than the target check its angle (opposite_ball_target)

        ball = np.array(self._match.ball)
        out = []
        for target in self.passable_robots:
            limit = distance_between_points(ball, target),
            out.append(min([angle_between_3_points(target, ball, opp)
                            for opp in self.intercepting_robots if distance_between_points(ball, opp) < limit],
                           default=math.pi))

        return [min(1, 4*i / math.pi) for i in out]

    def possession_change_probability(self):
        closest = min(map(lambda x: distance_between_points(x, self._robot), self.intercepting_robots))
        return 1 - min(1, closest/3)

    def goal_probability(self):
        robot_lock = (self._robot.x, 0)

        goal_posts = ((9, 2.5), (9, 3.5))
        goal_posts = (
            angle_between(self._robot, robot_lock, goal_posts[0]), angle_between(self._robot, robot_lock, goal_posts[1]))

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

        return 6*window / math.pi

    def pass_ex_value(self):
        action = []
        for v, p in zip(self.pass_value(), self.pass_probability()):
            # action.append(v * p - (1-p))  # consider loosing ball
            action.append(v * p)  # simple
            print(v, p)
        print('a', action)
        return action
