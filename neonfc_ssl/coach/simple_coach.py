import math
from neonfc_ssl.coach import BaseCoach
from neonfc_ssl.commons.math import distance_between_points
from neonfc_ssl.strategies import (BaseStrategy, Receiver, BallHolder, GoalKeeper, Libero, LeftBack, RightBack,
                                   PrepPenalty, PrepBallPlacement, PrepKickoff, PrepGKPenalty, PrepBHPenalty,
                                   PrepSecondKickoff)
from scipy.optimize import linear_sum_assignment
import numpy as np


class Coach(BaseCoach):
    NAME = "SimpleCoach"

    def _start(self):
        # Create strategies objects

        # Especial cases
        self._strategy_gk = GoalKeeper(self, self._match)
        self._strategy_bh = BallHolder(self, self._match)
        self._gk_id = 1

        # ------ n=6 ------ #
        # 1 fixed keeper
        #   when ball is inside area the keeper becomes the ball holder
        #
        # When ball-less
        # 3 defense robots (Libero/LeftBack/RightBack)
        # 1 ball holder
        # 1 fixed attacker
        #
        # When in possession
        # 2 defense robots
        # 1 ball holder
        # 2 attackers

        self._libero_strategies = {
            r_id: Libero(self, self._match, self.defensive_positions) for r_id in range(15)
        }

        self._left_back_strategy = LeftBack(self, self._match)
        self._right_back_strategy = RightBack(self, self._match)

        # Default attack strategies
        self._secondary_attack_strategies: dict[int, BaseStrategy] = {
            robot.robot_id: Receiver(self, self._match) for robot in self._match.robots if robot.robot_id != self._gk_id
        }
        self._secondary_attack_strategies[self._gk_id] = self._strategy_gk

        # Especial cases strategies
        self.ec_kickoff = PrepKickoff(self, self._match)
        self.ec_kickoff_secondary = PrepSecondKickoff(self, self._match)

        self.ec_penalty = {robot.robot_id: PrepPenalty(self, self._match) for robot in self._robots}
        self.ec_bh_penalty = PrepBHPenalty(self, self._match)
        self.ec_gk_penalty = PrepGKPenalty(self, self._match)

        self.prepare_freekick = PrepBallPlacement(self, self._match)

    def decide(self):
        if self.has_possession:
            self._defending()
        else:
            self._defending()

        if self._match.game_state.current_state.name != 'Run':
            self._fouls()

    def _fouls(self):
        # -- Stopped States -- #
        # * Stop
        # * BallPlacement
        # * PreparePenalty
        # * PrepareKickOff

        # -- Stop -- #
        # all robots must be outside a 0.5-meter range from the ball
        # in most cases it will only be an issue to the ball holder
        #
        # -- BallPlacement -- #
        # should not be an issue in the division B
        #
        # -- PreparePenalty -- #
        # keeper on the line
        # one attacker near the ball
        # all others 1 meter behind ball
        # all robots should change their behavior
        #
        # -- PrepareKickOff -- #
        # all robots on its sides
        # should only be a problem to the ball holder

        # -- Running Especial Cases -- #
        #
        # -- Penalty -- #
        # on penalty all non-participating robots (keeper and attacker)should stay in the prepare positions
        # ball holder could use a special strategy
        #
        # -- KickOff -- #
        # on kickoff only the one team may touch the ball
        # ball holder should keep the prepare strategy if on defense
        # ball holder could use a special strategy on attack
        #
        # -- FreeKick -- #
        # on kickoff only the one team may touch the ball
        # ball holder should have a different strategy
        # ball holder could use a special strategy on attack

        current_state = self._match.game_state.current_state.name
        our_team = self._match.game_state.current_state.color == self._match.team_color

        # Our kickoff
        if current_state in ['KickOff'] and our_team:
            for robot in self._active_robots:
                if robot.strategy.name != 'Ball Holder' and robot.robot_id != self._gk_id:
                    robot.set_strategy(self.ec_kickoff_secondary)
                    break

            for robot in self._active_robots:
                if robot.strategy.name == 'Ball Holder':
                    robot.set_strategy(self.ec_kickoff)
                    break

        if current_state in ['PrepareKickOff'] and our_team:
            for robot in self._active_robots:
                if robot.strategy.name != 'Ball Holder' and robot.robot_id != self._gk_id:
                    robot.set_strategy(self.ec_kickoff_secondary)
                    break

            for robot in self._active_robots:
                if robot.strategy.name == 'Ball Holder':
                    robot.set_strategy(self.prepare_freekick)
                    break

        # Their kickoff
        elif current_state in ['PrepareKickOff', 'KickOff'] and not our_team:
            for robot in self._active_robots:
                if robot.strategy.name == 'Ball Holder':
                    robot.set_strategy(self.ec_kickoff)
                    break

        # Our penalty
        elif current_state in ["PreparePenalty"] and our_team:
            for robot in self._active_robots:
                if robot.strategy.name == 'Ball Holder':
                    robot.set_strategy(self.ec_bh_penalty)

        ## If especial strategy to shoot penalty
        # elif current_state in ["Penalty"] and our_team:
        #     for robot in self._active_robots:
        #         if robot.strategy.name == 'Ball Holder':
        #             robot.set_strategy(self.ec_bh_penalty_shoot)

        # Their penalty
        elif current_state in ["PreparePenalty", "Penalty"] and not our_team:
            for robot in self._active_robots:
                if robot.robot_id == self._gk_id:
                    robot.set_strategy(self.ec_gk_penalty)
                else:
                    robot.set_strategy(self.ec_penalty[robot.robot_id])

        # Our free kick
        elif current_state in ['BallPlacement', 'Stop'] and our_team:
            for robot in self._active_robots:
                if robot.strategy.name == 'Ball Holder':
                    robot.set_strategy(self.prepare_freekick)
                    break

        # Their free kick
        elif current_state in ['BallPlacement', 'FreeKick', 'Stop'] and not our_team:
            for robot in self._active_robots:
                if robot.strategy.name == 'Ball Holder':
                    robot.set_strategy(self.prepare_freekick)
                    break

    def _defending(self):
        # when in possession check the ball carrier (smaller time to ball), than it becomes ball carrier
        new_carrier = self._closest_non_keeper()

        n_liberos = max(min(self._n_active_robots - 2, 3), 0)
        if n_liberos > 0:
            if self._use_left_back() or self._use_right_back():
                n_liberos -= 1

        use_cross_def, cross_def_pos = self.use_cross_def()
        if use_cross_def and n_liberos > 0:
            n_liberos -= 1

        pos = self._libero_y_positions(n_liberos)

        if n_liberos > 0:
            if self._use_left_back():
                pos = np.append(pos, [self._left_back_strategy.expected_position()], axis=0)
                n_liberos += 1
            if self._use_right_back():
                pos = np.append(pos, [self._right_back_strategy.expected_position()], axis=0)
                n_liberos += 1
            if use_cross_def:
                pos = np.append(pos, [cross_def_pos], axis=0)
                n_liberos += 1

        available_robots = self._clear_robot_list(self._active_robots[:], [self._gk_id, new_carrier])
        available_robots.sort(key=lambda r: r.x)

        liberos = available_robots[:n_liberos]
        # com dois robos essa lista retorna vazia crasha o codigo
        self.cost_matrix(pos, liberos)

        # the carrier receives its strategies and every other receives its secondary strategies
        for robot in self._robots:
            if robot.robot_id == new_carrier:
                robot.set_strategy(self._strategy_bh)
            elif robot.robot_id == self._gk_id:
                robot.set_strategy(self._strategy_gk)
            elif robot in liberos:
                robot.set_strategy(self._libero_strategies[robot.robot_id])
            else:
                robot.set_strategy(self._secondary_attack_strategies[robot.robot_id])

    def _use_shadow_defense(self):
        closest = min(self._match.active_opposites, key=lambda r: distance_between_points(r, self._match.ball), default=None)
        keeper = min(self._match.active_opposites, key=lambda r: distance_between_points(r, (self._match.field.fieldLength, self._match.field.fieldWidth/2)), default=None)

        def can_attack(r):
            if r == closest or r == keeper:
                return False

            if r.y > 0.75*self._match.field.fieldLength:
                return False

            return True

        if len(self._match.active_robots) - len(self._match.active_opposites) < 2:
            return False, None

        opps = self._match.active_opposites[:]
        opps.sort(key=lambda opp: opp.x)
        opps = list(filter(can_attack, opps))

        if len(opps) == 0:
            return False, None

        opp = opps[0]
        field = self._match.field
        ang = math.atan2(-opp.y + field.fieldWidth / 2, -opp.x)

        x = opp.x + math.cos(ang) * 0.65
        y = opp.y + math.sin(ang) * 0.65

        return True, (x, y)

    def _use_right_back(self):
        field = self._match.field
        limit = (field.fieldWidth - field.penaltyAreaWidth) / 2 + 0.2

        return self._match.ball.x < field.fieldLength / 3 and self._match.ball.y < limit

    def _use_left_back(self):
        field = self._match.field
        limit = (field.fieldWidth + field.penaltyAreaWidth) / 3 - 0.2

        return self._match.ball.x < field.fieldLength / 3 and self._match.ball.y > limit

    def _closest_non_keeper(self):
        def can_be_bh(r):
            double_kick = self._match.game_state.current_state.last_state
            if double_kick is not None and double_kick.first_touch:
                return r.robot_id != self._gk_id and r.robot_id != double_kick.first_touch_id
            else:
                return r.robot_id != self._gk_id

        sq_dist_to_ball = lambda r: np.sum(np.square(np.array(r) - self._match.ball)) if can_be_bh(r) else np.inf
        my_closest = min(self._match.active_robots, key=sq_dist_to_ball, default=None)
        if my_closest:
            return my_closest.robot_id
        else:
            return 1

    def _attacking(self):
        # when in possession check the ball carrier (smaller time to ball), than it becomes ball carrier
        new_carrier = self._closest_to_ball()

        # the carrier receives its strategies and every other receives its secondary strategies
        for robot in self._robots:
            if robot.robot_id == new_carrier:
                robot.set_strategy(self._strategy_bh)
            else:
                robot.set_strategy(self._secondary_attack_strategies[robot.robot_id])

    def _closest_to_ball(self):
        return self._match.possession.current_closest.robot_id

    def _closest_opponent(self):
        ball = self._match.ball

        closest = 100000
        for robot in self._match.opposites:
            dist = distance_between_points([ball.x, ball.y], [robot.x, robot.y])
            if dist < closest:
                closest = dist
                theta = robot.theta - math.pi
                x_robot = robot.x
                y_robot = robot.y
                data = [x_robot, y_robot, theta, closest]

        return data

    def _ball_proj(self, x_robot, y_robot, theta, closest):
        ball = self._match.ball
        field = self._match.field

        y_goal_min = (field.fieldWidth / 2) - field.goalWidth / 2
        y_goal_max = (field.fieldWidth / 2) + field.goalWidth / 2
        x = field.penaltyAreaDepth + 0.2

        y_max = ((y_goal_max - ball.y) / (-ball.x)) * (x - ball.x) + ball.y
        y_min = ((y_goal_min - ball.y) / (-ball.x)) * (x - ball.x) + ball.y
        if closest < 0.15:
            y = math.tan(theta) * (x - x_robot) + y_robot

        elif ball.x < field.leftPenaltyStretch[0] and ball.y < field.leftPenaltyStretch[1]:
            y = field.leftPenaltyStretch[1] - 0.2
            return y

        elif ball.x < field.leftPenaltyStretch[0] and ball.y > (field.fieldWidth - field.leftPenaltyStretch[1]):
            y = (field.fieldWidth - field.leftPenaltyStretch[1]) + 0.2
            return y

        elif abs(ball.vx) < 0.05:
            y = ball.y

        else:
            y = (ball.vy / ball.vx) * (x - ball.x) + ball.y

        y = y_max if y > y_max else y
        y = y_min if y < y_min else y

        return y

    def _libero_y_positions(self, n_robots):
        data = self._closest_opponent()
        x_op = data[0]
        y_op = data[1]
        theta = data[2]
        closest = data[3]

        ball = self._match.ball
        field = self._match.field
        target = self._ball_proj(x_op, y_op, theta, closest)
        desired_pos = np.zeros((n_robots, 2))
        x = field.penaltyAreaDepth + 0.2

        if n_robots == 1:
            desired_pos[0][0] = x
            desired_pos[0][1] = target
            return desired_pos

        else:
            diameter = 0.2
            target -= diameter / 2
            ang = math.atan2(ball.vx, ball.vy) if abs(ball.vx) > 0.05 else 0

            for i in range(0, n_robots):
                desired_pos[i][0] = x
                if 1.57 >= ang <= 3.14:
                    desired_pos[i][1] = target + (i * diameter)
                elif -3.14 <= ang <= -1.57:
                    desired_pos[i][1] = target - (i * diameter)
                else:
                    desired_pos[i][1] = target - (i * diameter)

            return desired_pos

    def cost_matrix(self, desired_pos, defensive_robots):
        n_robots = len(desired_pos)
        robot_pos = np.zeros((n_robots, 2))
        cost_matrix = np.zeros((n_robots, n_robots))

        i = 0
        for robot in defensive_robots:
            robot_pos[i][0] = robot.x
            robot_pos[i][1] = robot.y
            i += 1

        for i in range(0, n_robots):
            for j in range(0, n_robots):
                cost_matrix[i][j] = (robot_pos[i][0] - desired_pos[j][0]) ** 2 + (
                            robot_pos[i][1] - desired_pos[j][1]) ** 2

        lines, columns = linear_sum_assignment(cost_matrix)
        for robot, pos in zip(lines, columns):
            self.defensive_positions[defensive_robots[robot].robot_id] = desired_pos[pos]

    def use_cross_def(self):
        if self._n_active_robots < 5:
            return False, None

        mark_robots = [
            r for r in self._match.opposites
            if not r.missing and
               r.x < self._match.field.fieldLength / 3 and
               abs(r.y - self._match.ball.y) > self._match.field.fieldWidth / 3
        ]

        if len(mark_robots) == 0:
            return False, None

        if self._match.ball.y > self._match.field.fieldWidth / 2:
            mark_robots.sort(key=lambda r: r.y, reverse=False)
            return True, (self._match.field.penaltyAreaDepth + 0.2, mark_robots[0].y + 0.2)
        else:
            mark_robots.sort(key=lambda r: r.y, reverse=True)
            return True, (self._match.field.penaltyAreaDepth + 0.2, mark_robots[0].y - 0.2)

    @staticmethod
    def _clear_robot_list(robot_list: list, rm_id):
        if isinstance(rm_id, int):
            rm_id = [rm_id]

        for rm_robot in rm_id:
            for robot in robot_list:
                if robot.robot_id == rm_robot:
                    robot_list.remove(robot)

        return robot_list
