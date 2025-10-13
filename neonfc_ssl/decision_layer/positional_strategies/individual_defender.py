from typing import Union
from .positional_strategy import PositionalStrategy, POSITION, POSE

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData, TrackedRobot


MIN_DISTANCE_FROM_AREA = 0.18/2 + 0.1 # robot radius + margin
X_OFFSET = 0.5
Y_OFFSET = 0.5


class IndividualDefender(PositionalStrategy):
    @staticmethod
    def decide_position(data: "MatchData", ids: list[int]):
        n = len(ids)
        if n != 1:
            raise Exception(f"Can only decide IndividualDefender for 1 robot: {ids}")

        ball = data.ball
        field = data.field

        if ball.y > field.field_width/2:
            return IndividualDefender.get_lower_half_target(data)
        else:
            return IndividualDefender.get_upper_half_target(data)

    @staticmethod
    def get_upper_half_target(data: "MatchData"):
        field = data.field

        should_not_block = lambda r: r.y > field.field_width/2 and r.x < field.field_length/3
        opposites = data.opposites.active
        opposites = filter(should_not_block, opposites)
        target_robot = min(opposites, key=lambda r: r.y, default=None)

        if target_robot is None:
            return [(None, None)]

        x = IndividualDefender.get_target_x(data, target_robot)
        y = max(field.field_width/2, target_robot.y - Y_OFFSET)

        return [(x, y)]

    @staticmethod
    def get_lower_half_target(data: "MatchData"):
        field = data.field

        should_not_block = lambda r: r.y < field.field_width/2 and r.x < field.field_length/3
        opposites = data.opposites.active
        opposites = filter(should_not_block, opposites)
        target_robot = max(opposites, key=lambda r: r.y, default=None)

        if target_robot is None:
            return [(None, None)]

        x = IndividualDefender.get_target_x(data, target_robot)
        y = min(field.field_width/2, target_robot.y + Y_OFFSET)

        return [(x, y)]

    @staticmethod
    def get_target_x(data: "MatchData", target_robot: "TrackedRobot"):
        field = data.field
        return max(target_robot.x - X_OFFSET, field.penalty_depth + MIN_DISTANCE_FROM_AREA)
