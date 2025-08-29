import logging
import numpy as np
from math import sqrt, cos, sin
from neonfc_ssl.core import Layer
from neonfc_ssl.commons.math import reduce_ang
from neonfc_ssl.control_layer.path_planning import RRTPlanner, RRTStarPlanner
from .control_data import ControlData, RobotCommand

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.decision_layer.decision_data import DecisionData, RobotRubric
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class Control(Layer):
    def __init__(self, config, log_q, event_pipe) -> None:
        super().__init__("ControlLayer", config, log_q, event_pipe)

        self.KP = 1.5
        self.KP_ang = 2

    def _start(self):
        self.logger.info("Starting control module starting ...")

        self.logger.info("Control module started!")

    def _step(self, data: 'DecisionData'):
        out = []
        for command in data.commands:
            if command.target_pose is None:
                continue
            out.append(self.run_single_robot(data.world_model, command))
        return ControlData(commands=out)

    def run_single_robot(self, data: 'MatchData', command: 'RobotRubric') -> RobotCommand:
        robot = data.robots[command.id]
        field = data.field

        # Initialize RRT planner
        path_planner = RRTStarPlanner()
        path_planner.set_start((robot.x, robot.y))
        path_planner.set_goal(command.target_pose[:2])
        path_planner.set_speed((robot.vx, robot.vy))
        path_planner.set_map_area((field.field_length, field.field_width))

        # Collect obstacles
        obstacles = []

        # Add friendly goalkeeper area as obstacle points
        penalty_area_obstacles = RRTPlanner.create_rectangle_obstacles(
            (0, field.field_width / 2 - field.penalty_width / 2),
            field.penalty_depth,
            field.penalty_width
        )
        obstacles.extend(penalty_area_obstacles)

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
        path = path_planner.plan()

        # Get next point from path
        if path and len(path) > 1:
            next_point = path[1]  # First point is current position
        else:
            next_point = command.target_pose[:2]

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
            vel_angular=vel_angular
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
