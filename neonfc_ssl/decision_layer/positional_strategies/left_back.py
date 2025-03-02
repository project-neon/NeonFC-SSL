from positional_strategy import PositionalStrategy
from math import atan2, tan, pi
from neonfc_ssl.commons.math import distance_between_points

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.match.match_data import MatchData


# FIXME: fix field position that depends on PenaltyStretch

class LeftBack(PositionalStrategy):
    def decide(self, data, ids):
        n = len(ids)
        if n != 1:
            raise Exception("Can only decide LeftBack for 1 robot")

        robot = data.robots[ids[1]]
        ball = data.ball

        target_theta = atan2(-robot.y + ball.y, -robot.x + ball.x)
        return self.expected_position(data), target_theta

    @staticmethod
    def _closest_opponent(data: 'MatchData'):
        ball = data.ball

        closest = 100000
        for robot in data.opposites:
            dist = distance_between_points([ball.x, ball.y], [robot.x, robot.y])
            if dist < closest:
                closest = dist
                theta = robot.theta - pi
                x_robot = robot.xself
                y_robot = robot.y
                data = [x_robot, y_robot, theta, closest]
        return data

    def expected_position(self, data: 'MatchData'):
        return self._defense_pos(*self._closest_opponent(data))
    
    def _defense_pos(self, data: 'MatchData', x_robot, y_robot, theta, closest):
        y = self.y_position(data)
        x = self.x_position(data, x_robot, y_robot, theta, closest)

        return x, y

    def x_position(self, data: 'MatchData', x_robot, y_robot, theta, closest):
        ball = data.ball
        field = data.field

        # y = (field.fieldWidth - field.leftPenaltyStretch[1]) + 0.2
        # y = field.penaltyAreaWidth + ((field.fieldWidth-field.penaltyAreaWidth)/2) + 0.2

        # x_min = (y-ball.y)*((-ball.x)/(y_goal_max-ball.y))+ball.x
        # x_max = (y-ball.y)*((-ball.x)/(y_goal_min-ball.y))+ball.x

        y = self.y_position(data)
        x_min = 0.15
        x_max = field.leftPenaltyStretch[0]
        # x_max = field.penaltyAreaDepth

        if closest < 0.15:
            x = ((y - y_robot) * (1 / tan(theta))) + x_robot

        elif abs(ball.vx) < 0.05:
            x = ball.x

        else:
            x = ((y - ball.y) * (ball.vx / ball.vy)) + ball.x

        return max(x_min, min(x_max, x))

    @staticmethod
    def y_position(data: 'MatchData'):
        field = data.field
        return (field.field_width - field.leftPenaltyStretch[1]) + 0.2

