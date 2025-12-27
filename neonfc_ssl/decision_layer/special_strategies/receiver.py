from NeonPathPlanning.potential_fields import PotentialField, PointField, LineField
from .special_strategy import SpecialStrategy
from ..decision_data import RobotRubric
import math

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData, TrackedRobot


DT = 0.1


class Receiver(SpecialStrategy):
    def __init__(self, logger):
        super().__init__(logger)
        self.data = []

    def get_data(self):
        return self.data

    def _start(self):
        self.field = PotentialField(self.data)

        D = 4  # m
        L = 1

        for r in range(16):
            if r == self._robot_id:
                continue
            self.field.add_field(PointField(
                self.get_data,
                target=self.get_robot(r),
                radius_max=1,
                decay=lambda x: 1/x if x else 1/0.0001,
                multiplier=-0.5  # 50 cm/s
            ))

        for r in range(16):
            self.field.add_field(PointField(
                self.get_data,
                target=self.get_opposite(r),
                radius_max=0.3,  # 25 cm
                decay=lambda x: 1,
                multiplier=-10  # 50 cm/s
            ))
            self.field.add_field(LineField(
                self.get_data,
                target=self.get_opposite(r),
                theta=self.ang_robot_ball(r),
                inverse=True,
                line_size_single_side=True,
                line_size=D,
                multiplier=-1,
                decay=lambda x: 1,
                line_dist=L,
                line_dist_max=L
            ))

        self.field.add_field(PointField(
            self.get_data,
            target=self.get_ball(),
            decay=lambda x: 1,
            radius_max=20,
            multiplier=50  # 50 cm/s
        ))

        self.field.add_field(PointField(
            self.get_data,
            target=self.get_ball(),
            radius_max=2,
            decay=lambda x: 1,
            multiplier=-50  # 50 cm/s
        ))

    @staticmethod
    def get_robot(robot_id):
        def wrapped(data: list["MatchData"]):
            robot = data()[0].robots[robot_id]
            if robot.missing:
                return -10, -10

            return robot.x, robot.y
        return wrapped

    @staticmethod
    def get_opposite(robot_id):
        def wrapped(data: list["MatchData"]):
            robot = data()[0].opposites[robot_id]
            if robot.missing:
                return -10, -10

            return robot.x, robot.y
        return wrapped

    @staticmethod
    def get_ball():
        def wrapped(data: list["MatchData"]):
            ball = data()[0].ball

            return ball.x, ball.y
        return wrapped

    @staticmethod
    def ang_robot_ball(robot_id):
        def wrapped(data: list["MatchData"]):
            m = data()[0]
            robot = data()[0].opposites[robot_id]

            return math.pi - math.atan2(robot.y-m.ball.y, robot.x-m.ball.x)
        return wrapped

    def decide(self, data: "MatchData"):
        self.data = [data]
        robot = data.robots.active[self._robot_id]
        ball = data.ball
        vx, vy = self.field.compute([robot.x, robot.y])
        x = vx*DT + robot.x
        y = vy*DT + robot.y
        angle = math.atan2(-robot.y+ball.y, -robot.x+ball.x)

        return RobotRubric(
            id=self._robot_id,
            halt=False,
            target_pose=(x, y, angle)
        )
