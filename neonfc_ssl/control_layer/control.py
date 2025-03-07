import logging
import numpy as np
from math import sqrt, cos, sin
from neonfc_ssl.core import Layer
from neonfc_ssl.commons.math import reduce_ang
from neonfc_ssl.path_planning.drunk_walk import DrunkWalk
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
        self.log(logging.INFO, "Starting control module starting ...")

        self.log(logging.INFO, "Control module started!")

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

        path_planning = DrunkWalk()
        path_planning.start((robot.x, robot.y), command.target_pose[:2])

        post_thickness = 0.02
        goal_depht = 0.18
        goal_height = 1
        r = 0.09
        L = 12
        m = 0

        # -- Friendly Goalkeeper Area -- #
        if command.avoid_area:
            path_planning.add_static_obstacle(
                (0, field.field_width / 2 - field.penalty_width / 2),
                field.penalty_depth,
                field.penalty_width
            )
        # -- Friendly Goal Posts -- #
        path_planning.add_static_obstacle(
            (-r - goal_depht - post_thickness, field.field_width / 2 - r - goal_height / 2),
            2 * r + post_thickness + goal_depht,
            2 * r + goal_height
        )
        # -- Opponent Goalkeeper Area -- #
        path_planning.add_static_obstacle(
            (field.field_length - field.penalty_depth,
             field.field_width / 2 - field.penalty_width / 2),
            field.penalty_depth,
            field.penalty_width
        )
        # # -- Opponent Goal Posts -- #
        # path_planning.add_static_obstacle(
        #     (-1, -1),
        #     self._field.fieldLength + 2,
        #     0.7
        # )
        # -- Lower Field Limit -- #
        path_planning.add_static_obstacle(
            (-L - m, -L - m),
            field.field_length + 2 * (m + L),
            L + r
        )
        # -- Right Field Limit -- #
        path_planning.add_static_obstacle(
            (field.field_length + m - r, -m),
            L,
            field.penalty_width + 2 * m
        )
        # -- Upper Field Limit -- #
        path_planning.add_static_obstacle(
            (-L - m, field.field_width + m - r),
            field.field_length + 2 * (m + L),
            L
        )
        # -- Left Field Limit -- #
        path_planning.add_static_obstacle(
            (-L - m, -m),
            L + r,
            field.field_width + 2 * m
        )

        # -- Opponent Robots -- #
        for opp in command.avoid_opponents:
            opp = data.opposites[opp]
            path_planning.add_dynamic_obstacle(opp, 0.2, np.array((opp.vx, opp.vy)))

        # -- Friendly Robots -- #
        for rob in command.avoid_allies:
            if rob == command.id:
                continue

            rob = data.robots[rob]
            path_planning.add_dynamic_obstacle(rob, 0.2, np.array((rob.vx, rob.vy)))

        next_point = path_planning.find_path()

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
