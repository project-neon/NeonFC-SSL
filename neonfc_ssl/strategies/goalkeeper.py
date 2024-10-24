from neonfc_ssl.strategies.base_strategy import BaseStrategy
from neonfc_ssl.skills import *
from NeonPathPlanning import Point
from neonfc_ssl.commons.math import point_in_rect, distance_between_points, reduce_ang
from math import tan, pi, atan2


class GoalKeeper(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Goalkeeper', coach, match)

        self.field = self._match.field
        self.target = None

        self.states = {
            'pass': SimplePass(coach, match),
            'go_to_ball': GoToBall(coach, match),
            'move_to_pose': MoveToPose(coach, match)
        }

        def not_func(f):
            def wrapped():
                return not f()

            return wrapped

        self.states["move_to_pose"].add_transition(self.states["go_to_ball"], self.go_to_ball_transition)
        self.states["go_to_ball"].add_transition(self.states["pass"], self.pass_transition)
        self.states["go_to_ball"].add_transition(self.states["move_to_pose"], not_func(self.go_to_ball_transition))
        self.states["pass"].add_transition(self.states["move_to_pose"], self.move_to_pose_transition)

    def _start(self):
        self.active = self.states['move_to_pose']
        self.active.start(self._robot, target=self.defense_target)

    def decide(self):
        next = self.active.update()

        if next.name != "MoveToPose":
            self.active = next

            if self.active.name == "Pass":
                _passing_to = Point(5, 4)
                self.active.start(self._robot, target=_passing_to)

            else:
                self.active.start(self._robot)

        else:
            target = self.defense_target()
            self.active = next
            self.active.start(self._robot, target=target)

        return self.active.decide()

    # calcula os limites do y
    def limit_y(self, x, y):
        ball = self._match.ball
        # y_goal_min = 2.5 + 0.15
        # y_goal_max = 3.5 - 0.15
        y_goal_min = 0.2 + 0.1
        y_goal_max = 1.34 - 0.1

        y_max = ((y_goal_max - ball.y) / (-ball.x)) * (x - ball.x) + ball.y + 0.1
        y_min = ((y_goal_min - ball.y) / (-ball.x)) * (x - ball.x) + ball.y - 0.1
        new_y = max(min(y, y_max, y_goal_max), y_min, y_goal_min)
        return new_y


    # calcula a posição de defesa do robô
    def defense_target(self):
        ball = self._match.ball
        x = 0.2

        ang = atan2(-self._robot.y+self._match.ball.y, -self._robot.x+self._match.ball.x)

        # bola quase parada
        if ball.vx > 0.05:
            y = self.limit_y(x, ball.y)
            return [x, y, 0]

        # bola a frente do meio campo
        elif ball.x > self.field.halfwayLine[0]:
            return [x, self.field.fieldWidth/2, 0]

        # checa o robo adversario mais próximo
        closest = 100000
        for robot in self._match.opposites:
            dist = distance_between_points([ball.x, ball.y], [robot.x, robot.y])
            if dist < closest:
                closest = dist
                theta = reduce_ang(robot.theta - pi)
                x_robot = robot.x
                y_robot = robot.y

        # se o robo adversario mais prox da bola estiver perto (15 cm)
        if closest < 0.15:
            y = tan(theta) * (x - x_robot) + y_robot

        # bola quase parada
        elif abs(ball.vx) < 0.05:
            y = self.limit_y(x, ball.y)
            return [x, y, ang]

        # proj da bola (robo adversario longe)
        else:
            y = (ball.vy / ball.vx) * (x - ball.x) + ball.y

        y = self.limit_y(x, y)

        # gambiarra p defender mais rapido
        if y > self.field.fieldWidth/2:
            y += 0.09
        else:
            y -= 0.09

        return [x, y, ang]

    def ball_in_area(self):
        if (self._match.ball.x < 1) and (self._match.ball.y > 2) and (self._match.ball.y < 4):
            return True
        return False

    def move_to_pose_transition(self):
        is_in_rect = point_in_rect([self._match.ball.x, self._match.ball.y],
                                   [self.field.leftFirstPost[0], self.field.leftFirstPost[1],
                                    self.field.goalWidth, 2 * self.field.fieldLength])

        if not is_in_rect and self._match.ball.x <= self.field.halfwayLine[0]:
            return True
        return False

    def go_to_ball_transition(self):
        area_ymin = (self.field.fieldWidth - self.field.penaltyAreaWidth)/2
        area_ymax = area_ymin + self.field.penaltyAreaWidth

        if (self._match.ball.x < self.field.penaltyAreaDepth) and (self._match.ball.y > area_ymin) and (self._match.ball.y < area_ymax):
            return True
        return False

    def pass_transition(self):
        is_in_rect = point_in_rect([self._match.ball.x, self._match.ball.y],
                                   [self._robot.x - 0.15, self._robot.y - 0.15, 0.3, 0.3])

        if is_in_rect and self.ball_in_area():
            return True
        return False
