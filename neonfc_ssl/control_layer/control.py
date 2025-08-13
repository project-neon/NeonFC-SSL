import logging
import numpy as np
from math import sqrt, cos, sin
from neonfc_ssl.core import Layer
from neonfc_ssl.commons.math import reduce_ang
from neonfc_ssl.control_layer.path_planning.drunk_walk import DrunkWalk
from neonfc_ssl.control_layer.path_planning.rrt import RRT
from neonfc_ssl.control_layer.path_planning.velocity_obstacle import StarVO
from .control_data import ControlData, RobotCommand
from time import time
from statistics import fmean, median, mode

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.decision_layer.decision_data import DecisionData, RobotRubric
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class Control(Layer):
    def __init__(self, config, log_q, event_pipe) -> None:
        super().__init__("ControlLayer", config, log_q, event_pipe)

        self.KP = 1.5
        self.KP_ang = 2

        self.elapsed_time = []
        self.t = 1

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

        field_len = field.field_length
        field_wid = field.field_width
        border = 0.3

        x_min = -border
        y_min = -border
        x_max = field_len + border
        y_max = field_wid + border

        obstacles = []

        t0 = time()

        planner = StarVO(
            pos = (robot.x, robot.y),
            goal = command.target_pose[:2],
            vel = (robot.vx, robot.vy),
            max_vel = 2.0,
            radius = robot.R/2
        )

        walls = [
            ((x_min, y_min), (x_min, y_max)), # left wall
            ((x_min, y_max), (x_max, y_max)), # upper wall
            ((x_max, y_max), (x_max, y_min)), # right wall
            ((x_max, y_min), (x_min, y_min)) # lower wall
        ]

        if command.avoid_area:
            area_y_start = (field_wid - field.penalty_width) / 2

            walls.extend([
                ((0, area_y_start), (0, area_y_start + field.penalty_width)),
                ((0, area_y_start + field.penalty_width), (field.penalty_depth, area_y_start + field.penalty_width)),
                ((field.penalty_depth, area_y_start + field.penalty_width), (field.penalty_depth, area_y_start)),
                ((field.penalty_depth, area_y_start), (0, area_y_start)),

                ((field_len - field.penalty_depth, area_y_start), (field_len - field.penalty_depth, area_y_start + field.penalty_width)),
                ((field_len - field.penalty_depth, area_y_start + field.penalty_width), (field_len, area_y_start + field.penalty_width)),
                ((field_len, area_y_start + field.penalty_width), (field_len, area_y_start)),
                ((field_len, area_y_start), (field_len - field.penalty_depth, area_y_start)),
            ])

        planner.update_walls(walls)

        # -- Opponent Robots -- #
        for opp in command.avoid_opponents:
            opp = data.opposites[opp]
            obstacles.append((
                (opp.x, opp.y),
                (opp.vx, opp.vy),
                opp.R / 2,
                0
            ))

        # -- Friendly Robots -- #
        for rob in command.avoid_allies:
            if rob == command.id:
                continue

            rob = data.robots[rob]
            obstacles.append((
                (rob.x, rob.y),
                (rob.vx, rob.vy),
                rob.R / 2,
                0
            ))

        planner.update_dynamic_obstacles(obstacles)

        new_v = planner.update()

        self.elapsed_time.append(time() - t0)

        # if self.t % 100 == 0:
        #     print(f"Time mean  : {fmean(self.elapsed_time):3f}s")
        #     print(f"Time median: {median(self.elapsed_time):3f}s")
        #     print(f"Time mode  : {mode(self.elapsed_time):3f}s")
        #     print(f"Time min   : {min(self.elapsed_time):3f}s")
        #     print(f"Time max   : {max(self.elapsed_time):3f}s\n")
        #     self.elapsed_time = []

        self.t += 1

        dx = new_v[0] # next_point[0] - robot.x
        dy = new_v[1] # next_point[1] - robot.y

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
