import math
from neonfc_ssl.algorithms.fsm import State
from neonfc_ssl.commons.math import reduce_ang, distance_between_points
from neonfc_ssl.decision_layer.decision import RobotRubric
from .base_skill import BaseSkill

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


def angle_between(p1, p2, p3):
    return math.atan2(p3[1] - p1[1], p3[0] - p1[0]) - math.atan2(p2[1] - p1[1], p2[0] - p1[0])


class Wait(State):
    def start(self, robot_id: int, _):
        self.robot_id = robot_id

    def decide(self, data: "MatchData"):
        return RobotRubric(
            id=self.robot_id,
            halt=False,
            spinner=True
        )

    def check_complete(self, data: "MatchData"):
        ball = data.ball
        return ball.speed < 0.01


class StepBack(State):
    def start(self, robot_id: int, _):
        self.robot_id = robot_id

    def decide(self, data: "MatchData"):
        robot = data.robots[self.robot_id]
        ball = data.ball

        step_back_dist = 0.17
        angle = math.atan2(ball.y - robot.y, ball.x - robot.x)

        target = (ball.x - step_back_dist * math.cos(angle), ball.y - step_back_dist * math.sin(angle), angle)

        return RobotRubric(
            id=self.robot_id,
            halt=False,
            target_pose=target
        )

    def check_complete(self, data: "MatchData"):
        robot = data.robots[self.robot_id]
        ball = data.ball

        return ((robot.x - ball.x) ** 2 + (robot.x - ball.x) ** 2) ** .5 > 0.012


class TurnToPass(State):
    def start(self, robot_id, target):
        self.robot_id = robot_id
        self.ot = target
        self.target_angle = 0

    def decide(self, data: "MatchData"):
        robot = data.robots[self.robot_id]
        ball = data.ball

        step_back_dist = 0.15
        self.target_angle = math.atan2(self.ot[1] - ball.y, self.ot[0] - ball.x)
        current_angle = math.atan2(ball.y - robot.y, ball.x - robot.x)

        diff = reduce_ang(self.target_angle - current_angle)
        limit_dif = math.copysign(min(abs(diff), math.pi / 3), diff)
        actual_angle = current_angle + limit_dif

        pos = (
            ball.x - step_back_dist * math.cos(actual_angle),
            ball.y - step_back_dist * math.sin(actual_angle),
            math.atan2(ball.y - robot.y, ball.x - robot.x)
        )

        return RobotRubric(
            id=self.robot_id,
            halt=False,
            target_pose=pos
        )

    def check_complete(self, data: "MatchData"):
        # check in the robot is inside a cone behind the ball facing the target
        robot = data.robots[self.robot_id]
        ball = data.ball

        max_r = 0.15
        min_r = 0
        max_a = math.pi/24

        # angle check
        v1 = abs(reduce_ang(math.atan2(ball.y - robot.y, ball.x - robot.x) - self.target_angle)) < max_a

        # distance check
        v2 = min_r <= ((robot.x - ball.x) ** 2 + (robot.y - ball.y) ** 2) ** .5 <= max_r

        return v1 and v2


class StepForward(State):
    def start(self, robot_id, target):
        self.robot_id = robot_id
        self.target = target
        self.final_target = (0, 0, 0)

    def decide(self, data: "MatchData"):
        ball = data.ball

        step_forward_dist = 0.03
        angle = math.atan2(self.target[1] - ball.y, self.target[0] - ball.x)

        self.final_target = (
            ball.x - step_forward_dist * math.cos(angle),
            ball.y - step_forward_dist * math.sin(angle),
            angle
        )

        return RobotRubric(
            id=self.robot_id,
            halt=False,
            target_pose=self.final_target
        )

    def check_complete(self, data: "MatchData"):
        robot = data.robots[self.robot_id]
        return (robot.x - self.final_target[0]) ** 2 + (robot.y - self.final_target[1]) ** 2 < 0.08 ** 2


class PerformSimplePass(State):
    def __init__(self):
        super().__init__()
        self.reach_speed = 0
        self.g = 9.81
        self.miu = 0.05 * math.pi
        self.c = 0.7
        self.a_s = -14
        self.a_r = -0.7

    def start(self, robot_id, target):
        self.robot_id = robot_id
        self.target = target

    def decide(self, data: "MatchData"):
        robot = data.robots[self.robot_id]

        d = math.sqrt((robot.x - self.target[0]) ** 2 + (robot.y - self.target[1]) ** 2)

        # using simple constant acceleration method
        # vb = math.sqrt(self.reach_speed ** 2 + 2 * self.g * self.miu * d)

        # using two 2 state ball model
        s_f = (self.c ** 2 - 1) / self.a_s
        r_f = -self.c ** 2 / self.a_r
        vb = math.sqrt(2 * d / (s_f + r_f))

        vb = min(vb, 6.5)

        return RobotRubric(
            id=self.robot_id,
            halt=False,
            kick_speed=(vb, 0)
        )


class PerformChipPass(State):
    def __init__(self):
        super().__init__()
        self.reach_speed = 0
        self.g = 9.8
        self.vz = 2.5

    def start(self, robot_id, target):
        self.robot_id = robot_id
        self.target = target

    def decide(self, data: "MatchData"):
        robot = data.robots[self.robot_id]

        d = math.sqrt((robot.x - self.target.x) ** 2 + (robot.y - self.target.y) ** 2)
        t = 2 * self.vz / self.g
        vb = d / t

        return RobotRubric(
            id=self.robot_id,
            halt=False,
            kick_speed=(vb, self.vz)
        )


class SimplePass(BaseSkill):
    def __init__(self):
        super().__init__()

        self.wait = Wait()
        self.step_back = StepBack()
        self.turn = TurnToPass()
        self.step_forward = StepForward()
        self.passing = PerformSimplePass()

        self.wait.add_transition(self.step_back, self.wait.check_complete)
        self.step_back.add_transition(self.turn, self.step_back.check_complete)
        self.turn.add_transition(self.step_forward, self.turn.check_complete)
        self.step_forward.add_transition(self.passing, self.step_forward.check_complete)

        self.active = self.wait

    def _start(self, target):
        self.active = self.wait
        self.target = target
        self.active.start(self._robot_id, self.target)

    def decide(self, data):
        next = self.active.update(data)

        if next != self.active:
            self.active = next
            self.active.start(self._robot_id, self.target)

        return self.active.decide(data)

    @staticmethod
    def start_pass(robot, ball):
        return distance_between_points(robot, ball) < 0.1

    @staticmethod
    def stop_pass(robot, ball):
        return distance_between_points(robot, ball) > 0.15


class ChipPass(BaseSkill):
    def __init__(self):
        super().__init__()
        self.turn = TurnToPass()
        self.passing = PerformSimplePass()
        self.turn.add_transition(self.passing, self.turn.check_complete)

    def _start(self, target):
        self.active = self.turn
        self.target = target
        self.active.start(self._robot_id, self.target)

    def decide(self, data):
        next = self.active.update(data)

        if next != self.active:
            self.active = next
            self.active.start(self._robot_id, self.target)

        return self.active.decide(data)
