from NeonPathPlanning import Point
from neonfc_ssl.commons.math import point_in_rect, distance_between_points, reduce_ang
from math import tan, pi, atan2
from neonfc_ssl.decision_layer.skills import *
from neonfc_ssl.decision_layer.special_strategies.special_strategy import SpecialStrategy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData
    from ..skills.base_skill import BaseSkill


class GoalKeeper(SpecialStrategy):
    def __init__(self):
        super().__init__()
        self.target = None

        self.states: dict[str, 'BaseSkill'] = {
            'pass': SimplePass(),
            'go_to_ball': GoToBall(),
            'move_to_pose': MoveToPose()
        }

        def not_func(f):
            def wrapped(*args, **kwargs):
                return not f(*args, **kwargs)

            return wrapped

        self.states["move_to_pose"].add_transition(self.states["go_to_ball"], self.go_to_ball_transition)
        self.states["go_to_ball"].add_transition(self.states["pass"], self.pass_transition)
        self.states["go_to_ball"].add_transition(self.states["move_to_pose"], not_func(self.go_to_ball_transition))
        self.states["pass"].add_transition(self.states["move_to_pose"], self.move_to_pose_transition)

    def _start(self):
        self.active = self.states['move_to_pose']
        self.active.start(self._robot_id, target=self.defense)

    def decide(self, data: "MatchData"):
        next = self.active.update(data)

        if next.name != "MoveToPose":
            self.active = next

            if self.active.name == "Pass":
                _passing_to = Point(5, 4)
                self.active.start(self._robot_id, target=_passing_to)

            else:
                self.active.start(self._robot_id)

        else:
            target = self.defense(data)
            self.active = next
            self.active.start(self._robot_id, target=target)

        out = self.active.decide(data)
        out.ignore_area = True
        return out

    # calcula os limites do y
    def limit_y(self, data: "MatchData", x, y):
        ball = data.ball
        field = data.field

        y_goal_min = (field.field_width/2)-field.goal_width/2
        y_goal_max = (field.field_width/2)+field.goal_width/2

        y_max = ((y_goal_max - ball.y) / (-ball.x)) * (x - ball.x) + ball.y
        y_min = ((y_goal_min - ball.y) / (-ball.x)) * (x - ball.x) + ball.y

        new_y = max(min(y, y_max, y_goal_max), y_min, y_goal_min)
        return new_y
    
    def ball_proj(self, data: "MatchData", x=0.1):
        robot = data.robots[self._robot_id]
        ball = data.ball
        field = data.field

        ang = atan2(-robot.y+ball.y, -robot.x+ball.x)

        # bola quase parada
        if ball.vx > 0.05:
            y = self.limit_y(data, x, ball.y)
            return y

        # bola a frente do meio campo
        elif ball.x > field.field_length/2:
            return field.field_width/2

        # checa o robo adversario mais próximo
        # TODO: rewrite this using the built in min function
        closest = 100000
        for op in data.opposites:
            dist = distance_between_points([ball.x, ball.y], [op.x, op.y])
            if dist < closest:
                closest = dist
                theta = reduce_ang(op.theta - pi)
                x_robot = op.x
                y_robot = op.y

        # se o robo adversario mais prox da bola estiver perto (15 cm)
        if closest < 0.15:
            y = tan(theta) * (x - x_robot) + y_robot

        # bola quase parada
        elif abs(ball.vx) < 0.05:
            y = self.limit_y(data, x, ball.y)
            return y

        # proj da bola (robo adversario longe)
        else:
            y = (ball.vy / ball.vx) * (x - ball.x) + ball.y

        y = self.limit_y(data, x, y)

        return y
    
    def y(self, data: "MatchData", x, x0, y0):
        ball = data.ball
        y = ((x-ball.x)*((ball.y - y0)/(ball.x - x0))) + ball.y
        return y

    def defense(self, data: "MatchData"):
        robot = data.robots[self._robot_id]
        ball = data.ball
        field = data.field

        x = 0.1
        theta = atan2(-robot.y+ball.y, -robot.x+ball.x)
        ang = atan2(ball.vx, ball.vy) if abs(ball.vx) > 0.05 else 0

        lib_y = []
        lib_x = []
        # FIXME: This implementation does not work anymore
        # for rob in data.robots.active:
        #     if rob.strategy.name == 'Libero':
        #         lib_y.append(rob.y)
        #         lib_x.append(rob.x)

        if len(lib_y) == 1:
            dist_lib_desired = abs(lib_y[0] - self.ball_proj(data, field.penalty_depth + 0.2))
            
            if dist_lib_desired > 0.1:
                y = self.ball_proj(data)
            
            else:
                if 0 >= ang >= -1.57:
                    y = self.y(data, x, lib_x[0], lib_y[0]-0.1)
        
                elif -3.14 <= ang <= -1.57:
                    y = self.y(data, x, lib_x[0], lib_y[0]+0.1)
                
                else:
                    y = ball.y

        elif len(lib_y) > 1:
            lib_y.sort()
            dist_between_libs = abs(lib_y[1]-lib_y[0])
            dist_lib_desired = abs(lib_y[1] - self.ball_proj(data, field.penalty_depth + 0.2))
            
            if dist_lib_desired > 0.1 or dist_between_libs > 0.23:
                y = self.ball_proj(data)

            else:
                if 0 >= ang >= -1.57:
                    y = self.y(data, x, lib_x[0], max(lib_y)+0.1)
    
                elif -3.14 <= ang <= -1.57:
                    y = self.y(data, x, lib_x[0], min(lib_y)-0.1)

                else:
                    y = ball.y
        
        else:
            y = self.ball_proj(data)
        
        y = self.limit_y(data, x, y)

        return [x, y, theta]

    def ball_in_area(self, data: "MatchData"):
        ball = data.ball
        if (ball.x < 1) and (ball.y > 2) and (ball.y < 4):
            return True
        return False

    def move_to_pose_transition(self, data: "MatchData"):
        ball = data.ball
        field = data.field

        is_in_rect = point_in_rect(
            [ball.x, ball.y],
            [field.leftFirstPost[0], field.leftFirstPost[1],
             field.goal_width,
             2 * field.field_length]
        )

        if not is_in_rect and ball.x <= field.field_length/2:
            return True
        return False

    def go_to_ball_transition(self, data: "MatchData"):
        ball = data.ball
        field = data.field

        area_ymin = (field.field_width - field.penalty_width)/2
        area_ymax = area_ymin + field.penalty_width

        if (ball.x < field.penalty_depth) and (ball.y > area_ymin) and (ball.y < area_ymax):
            return True
        return False

    def pass_transition(self, data: "MatchData"):
        robot = data.robots[self._robot_id]
        ball = data.ball
        is_in_rect = point_in_rect([ball.x, ball.y],
                                   [robot.x - 0.15, robot.y - 0.15, 0.3, 0.3])

        if is_in_rect and self.ball_in_area(data):
            return True
        return False
