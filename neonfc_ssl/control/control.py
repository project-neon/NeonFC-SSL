import logging
import numpy as np
import time
import socket
from neonfc_ssl.entities import Field, RobotCommand
from neonfc_ssl.match.ssl_match import SSLMatch
from neonfc_ssl.coach import BaseCoach
from neonfc_ssl.commons.math import reduce_ang
from neonfc_ssl.path_planning.drunk_walk import DrunkWalk


class Control:
    def __init__(self, game) -> None:
        self.last_info = time.time()
        self._game = game

        # Previous Layer Classes
        self._match: SSLMatch = None
        self._field: Field = None
        self._coach: BaseCoach = None

        # Control Objects
        self.commands: list[RobotCommand] = None

        # Other Control Parameters
        # from pyvisgraph doc "Number of CPU cores on host computer. If you don't know how many
        # cores you have, use 'cat /proc/cpuinfo | grep processor | wc -l'"
        self._num_workers = 1

        self.KP = 1.5
        self.KP_ang = 2

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 5006

        self.new_data = False

        # Control Logger
        self.logger = logging.getLogger("control")

    def start(self):
        self.logger.info("Starting control module starting ...")

        # Get Last Layer Classes
        self._match = self._game.match
        self._field = self._match.field
        self._coach = self._game.coach

        self.logger.info("Control module started!")

    def update(self):
        self.commands = self._coach.commands
        all_paths = []

        for command in self.commands:
            if command.target_pose is None:
                continue

            path_planning = DrunkWalk()
            path_planning.start((command.robot.x, command.robot.y), command.target_pose[:2])

            post_thickness = 0.02
            goal_depht = 0.18
            goal_height = 1
            r = 0.09

            # -- Friendly Goalkeeper Area -- #
            path_planning.add_static_obstacle(
                (0, self._field.fieldWidth/2 - self._field.penaltyAreaWidth/2),
                self._field.penaltyAreaDepth,
                self._field.penaltyAreaWidth
            )
            # -- Friendly Goal Posts -- #
            path_planning.add_static_obstacle(
                (-r-goal_depht-post_thickness, self._field.fieldWidth/2 - r - goal_height/2),
                2*r + post_thickness + goal_depht,
                2*r + goal_height
            )
            # -- Opponent Goalkeeper Area -- #
            path_planning.add_static_obstacle(
                (self._field.fieldLength - self._field.penaltyAreaDepth, self._field.fieldWidth / 2 - self._field.penaltyAreaWidth/2),
                self._field.penaltyAreaDepth,
                self._field.penaltyAreaWidth
            )
            # -- Opponent Goal Posts -- #
            path_planning.add_static_obstacle(
                (-1, -1),
                self._field.fieldLength + 2,
                0.7
            )
            path_planning.add_static_obstacle(
                (self._field.fieldLength + 0.3, self._field.fieldWidth / 2 - r - goal_height / 2),
                2 * r + post_thickness + goal_depht,
                2 * r + goal_height
            )
            path_planning.add_static_obstacle(
                (self._field.fieldLength - r, self._field.fieldWidth / 2 - r - goal_height / 2),
                2 * r + post_thickness + goal_depht,
                2 * r + goal_height
            )
            path_planning.add_static_obstacle(
                (self._field.fieldLength - r, self._field.fieldWidth / 2 - r - goal_height / 2),
                2 * r + post_thickness + goal_depht,
                2 * r + goal_height
            )
            path_planning.add_static_obstacle(
                (self._field.fieldLength - r, self._field.fieldWidth / 2 - r - goal_height / 2),
                2 * r + post_thickness + goal_depht,
                2 * r + goal_height
            )

            # -- Opponent Robots --#
            [path_planning.add_dynamic_obstacle(r, 0.2, np.array((r.vx, r.vy))) for r in self._match.active_opposites]

            next_point = path_planning.find_path()

            dx = next_point[0] - command.robot.x
            dy = next_point[1] - command.robot.y

            dt = reduce_ang(command.target_pose[2] - command.robot.theta)

            command.move_speed = (dx*self.KP, dy*self.KP, dt*self.KP_ang)

        if time.time() - self.last_info > 0.1:
            self.last_info = time.time()
            paths = []
            for path in all_paths:
                paths.append(';'.join(f"%0.2f,%0.2f" % (point.x, point.y) for point in path))
            MESSAGE = 'a'.join(paths).encode('ascii')
            self.sock.sendto(MESSAGE, (self.UDP_IP, self.UDP_PORT))

        self.new_data = True
