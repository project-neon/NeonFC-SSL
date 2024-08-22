from neonfc_ssl.algorithms.fsm import State
from neonfc_ssl.entities import RobotCommand
from neonfc_ssl.skills.base_skill import BaseSkill
from neonfc_ssl.commons.math import reduce_ang
import math


def angle_between(p1, p2, p3):
    return math.atan2(p3[1] - p1[1], p3[0] - p1[0]) - math.atan2(p2[1] - p1[1], p2[0] - p1[0])


class TurnToShoot(State):
    def __init__(self):
        super().__init__()
        self.name = 'TurnToShoot'

    def start(self, robot):
        self.match = robot.match
        self.robot = robot
        self.target = self.find_best_shoot()

    def decide(self):
        desired = reduce_ang(self.target - self.robot.theta)
        kp = -9
        return RobotCommand(spinner=True, move_speed=(0, 0, desired*kp), robot_id=self.robot.robot_id)

    def check_complete(self):
        return abs(reduce_ang(self.target - self.robot.theta)) <= 0.05

    def find_best_shoot(self):
        robot_lock = (self.robot.x, 0)

        goal_posts = ((9, 2.5), (9, 3.5))
        goal_posts = (angle_between(self.robot, robot_lock, goal_posts[0]), angle_between(self.robot, robot_lock, goal_posts[1]))

        robot_angles = [angle_between(self.robot, robot_lock, robot)
                        for robot in self.match.opposites if robot.x > self.robot.x and not robot.missing]
        robot_angles.append(goal_posts[0])
        robot_angles.append(goal_posts[1])

        robot_angles.sort()
        robot_angles = list(filter(lambda x: goal_posts[0] <= x <= goal_posts[1], robot_angles))

        diffs = []

        for a, b in zip(robot_angles[:-1], robot_angles[1:]):
            diffs.append((a, b - a))

        initial, window = max(diffs, key=lambda x: x[1])

        return initial + (window-math.pi) / 2


class PerformShoot(State):
    def __init__(self):
        super().__init__()
        self.name = 'PerformShoot'

    def start(self, robot):
        self.match = robot.match
        self.robot = robot

    def decide(self):
        return RobotCommand(kick_speed=(6.5, 0), robot_id=self.robot.robot_id)


class Shoot(BaseSkill):
    def __init__(self, coach, match):
        super().__init__('Shoot', coach, match)
        self.turn = TurnToShoot()
        self.shoot = PerformShoot()
        self.turn.add_transition(self.shoot, self.turn.check_complete)
        self.active = None

    def _start(self):
        self.active = self.turn
        self.active.start(self._robot)

    def decide(self):
        next = self.active.update()

        if next != self.active:
            self.active = next
            self.active.start(self._robot)

        return self.active.decide()
