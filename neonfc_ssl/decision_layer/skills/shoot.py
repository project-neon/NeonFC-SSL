import math
from neonfc_ssl.algorithms.fsm import State
from neonfc_ssl.commons.math import reduce_ang
from neonfc_ssl.decision_layer.decision import RobotCommand
from base_skill import BaseSkill

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.match.match_data import MatchData


def angle_between(p1, p2, p3):
    return math.atan2(p3[1] - p1[1], p3[0] - p1[0]) - math.atan2(p2[1] - p1[1], p2[0] - p1[0])


class TurnToShoot(State):
    def start(self, robot_id, target):
        self.robot_id = robot_id
        self.target = target

    def decide(self, data: "MatchData"):
        robot = data.robots[self.robot_id]

        desired = reduce_ang(self.target - robot.theta)
        kp = -9
        # return RobotCommand(spinner=True, move_speed=(0, 0, desired*kp), robot=self.robot)

        return

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
        return RobotCommand(move_speed=(0, 0, 0), kick_speed=(6.5, 0), robot=self.robot)


class Shoot(BaseSkill):
    def decide(self, data):
        pass
