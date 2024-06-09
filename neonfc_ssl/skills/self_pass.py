from neonfc_ssl.algorithms.fsm import State
from neonfc_ssl.entities import RobotCommand
import math


def angle_between(p1, p2, p3):
    return math.atan2(p3[1] - p1[1], p3[0] - p1[0]) - math.atan2(p2[1] - p1[1], p2[0] - p1[0])


def reduce_angle(ang):
    while ang > math.pi:
        ang -= 2 * math.pi
    while ang < -math.pi:
        ang += 2 * math.pi
    return ang


class TurnToPass(State):
    def __init__(self):
        super().__init__()
        self.name = 'TurnToPass'

    def start(self, robot, target):
        self.match = robot.match
        self.robot = robot
        self.target = target

    def decide(self):
        target = math.atan2(self.target.y - self.robot.y, self.target.x - self.robot.x)
        desired = reduce_angle(target - self.robot.theta)
        kp = -9
        return RobotCommand(spinner=True, move_speed=(0, 0, desired*kp), robot_id=self.robot.robot_id)

    def check_complete(self):
        target = math.atan2(self.target.y - self.robot.y, self.target.x - self.robot.x)
        return abs(reduce_angle(target - self.robot.theta)) <= 0.02


class PerformSimplePass(State):
    def __init__(self):
        super().__init__()
        self.name = 'PerformSimplePass'
        self.reach_speed = 0
        self.g = 9.81
        self.miu = 0.05*math.pi #  .25

    def start(self, robot, target):
        self.match = robot.match
        self.robot = robot
        self.target = target

    def decide(self):
        d = math.sqrt((self.robot.x - self.target.x)**2 + (self.robot.y - self.target.y)**2)
        vb = math.sqrt(self.reach_speed**2 + 2*self.g*self.miu*d)
        return RobotCommand(kick_speed=(vb, 0), robot_id=self.robot.robot_id)


class PerformChipPass(State):
    def __init__(self):
        super().__init__()
        self.name = 'PerformShoot'
        self.reach_speed = 0
        self.g = 9.8
        self.vz = 2.5

    def start(self, robot, target):
        self.match = robot.game.match
        self.robot = robot
        self.target = target

    def decide(self):
        d = math.sqrt((self.robot.x - self.target.x)**2 + (self.robot.y - self.target.y)**2)
        t = 2*self.vz/self.g
        vb = d/t
        return RobotCommand(kick_speed=(vb, self.vz))


class Pass(State):
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
