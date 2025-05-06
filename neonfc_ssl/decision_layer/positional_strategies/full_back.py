from .positional_strategy import PositionalStrategy
from math import atan2, tan, pi
from neonfc_ssl.commons.math import angle_to_first_quadrant, angle_between

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class FullBack:
    @staticmethod
    def _decide(data: 'MatchData', ids: list[int], left: bool):
        # Parameters
        DISTANCE_FROM_AREA = 0.18 / 2 + 0.1  # robot radius + margin
        MAX_X_DISTANCE = 0.18 / 2  # robot radius
        USE_OP_DIST_TOLERANCE = 0.15
        USE_OP_ANGLE_TOLERANCE = pi / 12  # 15°
        USE_BALL_SPEED_TOLERANCE = 0.5

        n = len(ids)
        ball = data.ball
        field = data.field

        sq_dist_to_ball = lambda r: (r.x - ball.x) ** 2 + (r.y - ball.y) ** 2
        angle_to_ball_delta = lambda r: abs(angle_to_first_quadrant(angle_between(r, ball) - r.theta))
        closest_op = min(data.opposites.active, key=sq_dist_to_ball, default=None)

        use_op_angle = (
                sq_dist_to_ball(closest_op) < USE_OP_DIST_TOLERANCE
                and angle_to_ball_delta(closest_op) < USE_OP_ANGLE_TOLERANCE
                and pi / 2 < angle_to_ball_delta(closest_op) < 3 * pi / 2
        ) if closest_op else False
        use_ball_speed = ball.speed > USE_BALL_SPEED_TOLERANCE and ball.vx < 0

        y = field.field_width/2 + field.penalty_width/2 + DISTANCE_FROM_AREA if left \
            else field.field_width/2 - field.penalty_width/2 - DISTANCE_FROM_AREA

        if use_op_angle:
            x_projection = (-tan(closest_op.theta) * (y - ball.y)) + ball.x
        elif use_ball_speed:
            x_projection = (ball.vx / ball.vy * (y - ball.y)) + ball.x
        else:
            x_projection = ball.x

        lower_area_limit = 0.18/2
        upper_area_limit = field.penalty_depth + MAX_X_DISTANCE

        x_projection = max(x_projection, 0)
        x_projection = min(x_projection, upper_area_limit)

        total_coverage = n * 0.18  # robot diameter

        if total_coverage > upper_area_limit - lower_area_limit:
            raise ValueError("Can't position this many fullbacks")

        angle = pi/2 if left else -pi/2

        if total_coverage / 2 + x_projection > upper_area_limit:
            poses = [(upper_area_limit - 0.18 * i, y, angle) for i in range(n)]

        elif -total_coverage/2 + x_projection < lower_area_limit:
            poses = [(lower_area_limit + 0.18*i, y, angle) for i in range(n)]

        elif n % 2:
            poses = [(x_projection + 0.18 * i, y, angle) for i in range(-int(n / 2), int(n / 2) + 1)]

        else:
            poses = [(x_projection + 0.18 / 2 + 0.18 * i, y, angle) for i in range(-int(n / 2), int(n / 2))]

        return poses
