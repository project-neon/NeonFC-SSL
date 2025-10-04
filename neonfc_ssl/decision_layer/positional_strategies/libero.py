from math import pi, tan
from .positional_strategy import PositionalStrategy
from neonfc_ssl.commons.math import angle_to_first_quadrant, angle_between
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class Libero(PositionalStrategy):
    @staticmethod
    def decide_position(data: 'MatchData', ids: list[int]):
        # Parameters
        DISTANCE_FROM_AREA = 0.18/2 + 0.1 # robot radius + margin
        MAX_Y_DISTANCE = 0.18/2 # robot radius
        USE_OP_DIST_TOLERANCE = 0.15
        USE_OP_ANGLE_TOLERANCE = pi/12 # 15°
        USE_BALL_SPEED_TOLERANCE = 0.5

        n = len(ids)
        ball = data.ball
        field = data.field

        sq_dist_to_ball = lambda r: (r.x-ball.x)**2 + (r.y-ball.y)**2
        angle_to_ball_delta = lambda r: abs(angle_to_first_quadrant(angle_between(r, ball)-r.theta))
        closest_op = min(data.opposites.active, key=sq_dist_to_ball, default=None)

        use_op_angle = (
                sq_dist_to_ball(closest_op) < USE_OP_DIST_TOLERANCE
                and angle_to_ball_delta(closest_op) < USE_OP_ANGLE_TOLERANCE
                and pi/2 < angle_to_ball_delta(closest_op) < 3*pi/2
        ) if closest_op else False
        use_ball_speed = ball.speed > USE_BALL_SPEED_TOLERANCE and ball.vx < 0

        x = field.penalty_depth + DISTANCE_FROM_AREA

        if use_op_angle:
            y_projection = (tan(closest_op.theta) * (x - ball.x)) + ball.y
        elif use_ball_speed:
            y_projection = (ball.vy/ball.vx * (x - ball.x)) + ball.y
        else:
            y_projection = ball.y

        lower_area_limit = field.field_width/2 - field.penalty_width/2 - MAX_Y_DISTANCE
        upper_area_limit = field.field_width/2 + field.penalty_width/2 + MAX_Y_DISTANCE

        y_projection = max(y_projection, lower_area_limit)
        y_projection = min(y_projection, upper_area_limit)

        total_coverage = n * 0.18 # robot diameter

        if total_coverage/2 + y_projection > upper_area_limit:
            poses = [(x, upper_area_limit - 0.18*i, 0) for i in range(n)]

        elif - total_coverage/2 + y_projection < lower_area_limit:
            poses = [(x, lower_area_limit + 0.18*i, 0) for i in range(n)]

        elif n%2:
            poses = [(x, y_projection + 0.18*i, 0) for i in range(-int(n/2), int(n/2)+1)]

        else:
            poses = [(x, y_projection + 0.18/2 + 0.18*i, 0) for i in range(-int(n/2), int(n/2))]

        return poses
