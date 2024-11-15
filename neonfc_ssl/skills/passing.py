from neonfc_ssl.algorithms.fsm import State
from neonfc_ssl.skills.base_skill import BaseSkill
from neonfc_ssl.entities import RobotCommand, OmniRobot
from neonfc_ssl.commons.math import reduce_ang, distance_between_points
import math


def angle_between(p1, p2, p3):
    return math.atan2(p3[1] - p1[1], p3[0] - p1[0]) - math.atan2(p2[1] - p1[1], p2[0] - p1[0])


class Wait(State):
    def __init__(self):
        super().__init__()
        self.name = 'Wait'

    def start(self, robot: OmniRobot, _):
        self.robot = robot

    def decide(self):
        return RobotCommand(spinner=True, robot=self.robot, move_speed=(0, 0, 0))

    def check_complete(self):
        return self.robot.match.ball.get_speed() < 0.03


class StepBack(State):
    def __init__(self):
        super().__init__()
        self.name = 'StepBack'

    def start(self, robot: OmniRobot, _):
        self.robot = robot

    def decide(self):
        r = self.robot
        b = self.robot.match.ball

        step_back_dist = 0.17
        angle = math.atan2(b.y - r.y, b.x - r.x)

        target = (b.x - step_back_dist * math.cos(angle), b.y - step_back_dist * math.sin(angle), angle)

        return RobotCommand(target_pose=target, robot=self.robot)

    def check_complete(self):
        r = self.robot
        b = self.robot.match.ball

        return ((r.x - b.x) ** 2 + (r.x - b.x) ** 2) ** .5 > 0.012


class TurnToPass(State):
    def __init__(self):
        super().__init__()
        self.name = 'TurnToPass'

    def start(self, robot, target):
        self.robot = robot
        self.ot = target
        self.target_angle = 0

    def decide(self):
        r = self.robot
        b = self.robot.match.ball

        step_back_dist = 0.15
        self.target_angle = math.atan2(self.ot[1] - b.y, self.ot[0] - b.x)
        current_angle = math.atan2(b.y - r.y, b.x - r.x)

        diff = reduce_ang(self.target_angle - current_angle)
        limit_dif = math.copysign(min(abs(diff), math.pi / 3), diff)
        actual_angle = current_angle + limit_dif

        pos = (
            b.x - step_back_dist * math.cos(actual_angle),
            b.y - step_back_dist * math.sin(actual_angle),
            math.atan2(b.y - r.y, b.x - r.x)
        )

        return RobotCommand(target_pose=pos, robot=self.robot)

    def check_complete(self):
        # check in the robot is inside a cone behind the ball facing the target
        r = self.robot
        b = self.robot.match.ball

        max_r = 0.15
        min_r = 0
        max_a = math.pi/24

        # angle check
        v1 = abs(reduce_ang(math.atan2(b.y - r.y, b.x - r.x) - self.target_angle)) < max_a

        # distance check
        v2 = min_r <= ((r.x - b.x) ** 2 + (r.y - b.y) ** 2) ** .5 <= max_r

        return v1 and v2


class StepForward(State):
    def __init__(self):
        # May benefit from the use of a kick sensor
        super().__init__()
        self.name = 'StepForward'

    def start(self, robot, target):
        self.robot = robot
        self.target = target
        self.final_target = (0, 0, 0)

    def decide(self):
        b = self.robot.match.ball

        step_forward_dist = 0.03
        angle = math.atan2(self.target[1] - b.y, self.target[0] - b.x)

        self.final_target = (b.x - step_forward_dist * math.cos(angle), b.y - step_forward_dist * math.sin(angle), angle)

        return RobotCommand(target_pose=self.final_target, robot=self.robot)

    def check_complete(self):
        return (self.robot.x - self.final_target[0]) ** 2 + (self.robot.y - self.final_target[1]) ** 2 < 0.08 ** 2


class PerformSimplePass(State):
    def __init__(self):
        super().__init__()
        self.name = 'PerformSimplePass'
        self.reach_speed = 0
        self.g = 9.81
        self.miu = 0.05 * math.pi
        self.c = 0.7
        self.a_s = -14
        self.a_r = -0.7

    def start(self, robot, target):
        self.robot = robot
        self.target = target

    def decide(self):
        d = math.sqrt((self.robot.x - self.target[0]) ** 2 + (self.robot.y - self.target[1]) ** 2)

        # using simple constant acceleration method
        # vb = math.sqrt(self.reach_speed ** 2 + 2 * self.g * self.miu * d)

        # using two 2 state ball model
        s_f = (self.c ** 2 - 1) / self.a_s
        r_f = -self.c ** 2 / self.a_r
        vb = math.sqrt(2 * d / (s_f + r_f))

        vb = min(vb, 6.5)

        return RobotCommand(move_speed=(0, 0, 0), kick_speed=(vb, 0), robot=self.robot)


class PerformChipPass(State):
    def __init__(self):
        super().__init__()
        self.name = 'PerformShoot'
        self.reach_speed = 0
        self.g = 9.8
        self.vz = 2.5

    def start(self, robot, target):
        self.robot = robot
        self.target = target

    def decide(self):
        d = math.sqrt((self.robot.x - self.target.x) ** 2 + (self.robot.y - self.target.y) ** 2)
        t = 2 * self.vz / self.g
        vb = d / t
        return RobotCommand(kick_speed=(vb, self.vz), robot_id=self.robot.robot_id)


class SimplePass(BaseSkill):
    def __init__(self, coach, match):
        super().__init__('Pass', coach, match)

        self.wait = Wait()
        self.step_back = StepBack()
        self.turn = TurnToPass()
        self.step_forward = StepForward()
        self.passing = PerformSimplePass()

        self.wait.add_transition(self.step_back, self.wait.check_complete)
        self.step_back.add_transition(self.turn, self.step_back.check_complete)
        self.step_back.add_transition(self.step_forward, self.turn.check_complete)
        self.turn.add_transition(self.step_forward, self.turn.check_complete)
        self.step_forward.add_transition(self.passing, self.step_forward.check_complete)

        self.active = self.wait

    def _start(self, target):
        self.active = self.wait
        self.target = target
        self.active.start(self._robot, self.target)

    def decide(self):
        next = self.active.update()

        if next != self.active:
            self.active = next
            self.active.start(self._robot, self.target)

        return self.active.decide()

    @staticmethod
    def start_pass(robot, ball):
        return distance_between_points(robot, ball) < 0.1

    @staticmethod
    def stop_pass(robot, ball):
        return distance_between_points(robot, ball) > 0.18


class ChipPass(State):
    def __init__(self):
        super().__init__()
        self.name = 'Pass'

        self.turn = TurnToPass()
        self.passing = PerformSimplePass()
        self.turn.add_transition(self.passing, self.turn.check_complete)

    def start(self, robot, target):
        self.robot = robot
        self.active = self.turn
        self.target = target

        self.active.start(self.robot, self.target)

    def decide(self):
        next = self.active.update()

        if next != self.active:
            self.active = next
            self.active.start(self.robot, self.target)

        return self.active.decide()
