import logging
from math import sqrt, cos, sin
from neonfc_ssl.core import Layer
from neonfc_ssl.commons.math import reduce_ang, point_in_rect
from .control_data import ControlData, RobotCommand
from .path_planning import PLANNERS

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.decision_layer.decision_data import DecisionData, RobotRubric
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class Control(Layer):
    def __init__(self, config, log_q) -> None:
        super().__init__("ControlLayer", config, log_q)

        self.KP = 1.5
        self.KP_ang = 2

    def _start(self):
        self.logger.info("Starting control module starting ...")

        self.__planner = PLANNERS[self.config["planner"]]

        self.logger.info("Control module started!")

    def _step(self, data: 'DecisionData'):
        out = []
        for command in data.commands:
            if command.halt:
                out.append(RobotCommand(
                    id=command.id,
                    is_yellow=data.world_model.is_yellow,
                    vel_normal=0,
                    vel_tangent=0,
                    vel_angular=0,
                    kick_x=0,
                ))
                continue
            if command.target_pose is not None:
                out.append(self.run_single_robot(data.world_model, command))
            elif command.kick_speed[0] > 0 or command.kick_speed[1] > 0:
                out.append(RobotCommand(
                    id=command.id,
                    is_yellow=data.world_model.is_yellow,
                    vel_normal=0,
                    vel_tangent=0,
                    vel_angular=0,
                    kick_x=command.kick_speed[0],
                ))
        return ControlData(commands=out)

    def run_single_robot(self, data: 'MatchData', command: 'RobotRubric') -> RobotCommand:
        robot = data.robots[command.id]
        field = data.field
        pos = (robot.x, robot.y)

        # Initialize Planner
        path_planner = self.__planner()
        path_planner.set_start((robot.x, robot.y))
        path_planner.set_goal(command.target_pose[:2])
        path_planner.set_velocity((robot.vx, robot.vy))
        path_planner.set_map_area((field.field_length, field.field_width))

        # Redirects target if it falls inside the friendly area (robot outside, target inside).
        if command.avoid_area and not point_in_rect(pos, path_planner.friendly_area) \
                and point_in_rect(command.target_pose[:2], path_planner.friendly_area):                
            x_0, y_0, area_len, area_wid = path_planner.friendly_area   # (-0.3, 2.0, 1.3, 2.0)
            
            x_border = x_0 + area_len + 0.1
            y_original = command.target_pose[1]
            y_redirected = max(y_0, min(y_0 + area_wid, y_original))
            path_planner.set_goal((x_border, y_redirected))

        # Forces robot out if it's already inside the friendly area.
        if command.avoid_area and point_in_rect(pos, path_planner.friendly_area):
            x_0, y_0, area_len, area_wid = path_planner.friendly_area   # (-0.3, 2.0, 1.3, 2.0)

            # Calculates the distance from each border and redirects the target out from the closest one.
            x_border = x_0 + area_len
            y_upper_border = y_0 + area_wid
            y_lower_border = y_0

            dist_right = abs(pos[0] - x_border)
            dist_upper = abs(pos[1] - y_upper_border)
            dist_lower = abs(pos[1] - y_lower_border)

            min_dist = min(dist_right, dist_upper, dist_lower)

            if min_dist == dist_upper:
                path_planner.set_goal((robot.x, y_upper_border + 0.1))
            elif min_dist == dist_lower:
                path_planner.set_goal((robot.x, y_lower_border - 0.1))
            else:
                path_planner.set_goal((x_border + 0.1, robot.y))
            
            # TODO: Robots can get stuck on the friendly area sides (lower and upper borders) when
            #       the area walls (obstacles) is between them and their target (HRVO is inefficient when
            #       dealing with walls).
            #       SOLUTION: Implementing a global pathplanner (RRT, already implemented on our repository) to
            #                 route around the area correctly.

        if point_in_rect(pos, (0.0, 0.0, field.field_length, field.field_width)):
            path_planner.add_field_walls(
                origin=0.0,
                border=0.0
            )

        if command.avoid_area and not point_in_rect(pos, path_planner.friendly_area):
            path_planner.add_friendly_area_walls()

        if not point_in_rect(pos, path_planner.opponent_area):
            path_planner.add_opp_area_walls()

        obstacles = []

        # Add opponent robots as obstacles
        for opp in command.avoid_opponents:
            opp_robot = data.opposites[opp]
            obstacles.append((opp_robot.x, opp_robot.y))

        # Add friendly robots as obstacles
        for rob in command.avoid_allies:
            if rob == command.id:
                continue
            friendly_robot = data.robots[rob]
            obstacles.append((friendly_robot.x, friendly_robot.y))

        path_planner.set_obstacles(obstacles)

        next_point = path_planner.plan()

        dx = next_point[0] - robot.x
        dy = next_point[1] - robot.y

        dt = reduce_ang(command.target_pose[2] - robot.theta)

        vel_x, vel_y, vel_theta = dx * self.KP, dy * self.KP, dt * self.KP_ang
        vel_tangent, vel_normal, vel_angular = self.global_speed_to_local_speed(vel_x, vel_y, vel_theta, robot)

        return RobotCommand(
            id=command.id,
            is_yellow=data.is_yellow,
            vel_normal=vel_normal,
            vel_tangent=vel_tangent,
            vel_angular=vel_angular,
            kick_x=command.kick_speed[0],
        )

        # if self._game_state.is_stopped():
        #     command.limit_speed(1.5)

    @staticmethod
    def global_speed_to_local_speed(vx, vy, w, robot):
        theta = robot.theta

        r_x = vx * cos(theta) + vy * sin(theta)
        r_y = -vx * sin(theta) + vy * cos(theta)

        L = 0.0785
        r = 0.03

        wheel = ((2 * L * abs(w)) + (sqrt(3) * abs(r_x)) + (sqrt(3) * abs(r_y))) / (2 * r)
        wheel_max = 40

        reducing_factor = min(wheel_max / wheel, 1) if wheel != 0 else 1

        return r_x * reducing_factor, r_y * reducing_factor, w * reducing_factor
