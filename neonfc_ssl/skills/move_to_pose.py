from neonfc_ssl.algorithms.fsm import State
from neonfc_ssl.entities import RobotCommand
from NeonPathPlanning import UnivectorField, Point


class MoveToPose(State):
    def __init__(self, robot, target):
        super().__init__()
        self.name = 'MoveToPose'
        self.match = robot.match
        self.robot = robot
        self.target = target

    def start(self, robot):
        self.robot = robot

        self.univector = UnivectorField(n=10, rect_size=.1)
        self.univector.set_target(Point(self.target[0], self.target[1]), self.target[2], 'a')

        for robot in self.match.robots:
            if robot == self.robot:
                continue
            self.univector.add_obstacle(robot, 0.25)

        for robot in self.match.opposites:
            self.univector.add_obstacle(robot, 0.25)

    def decide(self):
        return self.univector.compute(self.robot)
