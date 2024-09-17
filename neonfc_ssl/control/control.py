import math
import pyvisgraph as vg
import time
import socket

from neonfc_ssl.entities import Field, RobotCommand
from neonfc_ssl.match.ssl_match import SSLMatch
from neonfc_ssl.coach import BaseCoach
from neonfc_ssl.commons.math import reduce_ang, distance_between_points


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
        self.meta: dict = None
        self.vis_graph: vg.VisGraph = None
        self._field_poly: list[list[vg.Point]] = None

        # Other Control Parameters
        # from pyvisgraph doc "Number of CPU cores on host computer. If you don't know how many
        # cores you have, use 'cat /proc/cpuinfo | grep processor | wc -l'"
        self._num_workers = 8

        self.KP = 2
        self.KP_ang = 1.5  # -9

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 5006

        self.new_data = False

    def start(self):
        print("Starting control module starting ...")

        # Get Last Layer Classes
        self._match = self._game.match
        self._field = self._match.field
        self._coach = self._game.coach

        r = 0.09
        h05 = self._field.fieldWidth / 2

        # Create Layer
        self.vis_graph = vg.VisGraph()
        self._field_poly = [[
            # -- Field Limits -- #
            vg.Point(-0.3 + r, -0.3 + r),
            vg.Point(self._field.fieldLength + 0.3 - r, -0.3 + r),
            vg.Point(self._field.fieldLength + 0.3 - r, self._field.fieldWidth + 0.3 - r),
            vg.Point(-0.3 + r, self._field.fieldWidth + 0.3 - r)
        ], [
            # -- Opponent Goal Posts -- #
            vg.Point(self._field.fieldLength - r, h05 - 0.52 - r),
            vg.Point(self._field.fieldLength - (-0.2 - r), h05 - 0.52 - r),
            vg.Point(self._field.fieldLength - (-0.2 - r), h05 + 0.52 + r),
            vg.Point(self._field.fieldLength - r, h05 + 0.52 + r),
            vg.Point(self._field.fieldLength - r, h05 + 0.5 - r),
            vg.Point(self._field.fieldLength - (r - 0.18), h05 + 0.5 - r),
            vg.Point(self._field.fieldLength - (r - 0.18), h05 - 0.5 + r),
            vg.Point(self._field.fieldLength - r, h05 - 0.5 + r)
        ], [
            # -- Friendly Goal Posts -- #
            vg.Point(r, h05 - 0.52 - r),
            vg.Point(-0.2 - r, h05 - 0.52 - r),
            vg.Point(-0.2 - r, h05 + 0.52 + r),
            vg.Point(r, h05 + 0.52 + r),
            vg.Point(r, h05 + 0.5 - r),
            vg.Point(r - 0.18, h05 + 0.5 - r),
            vg.Point(r - 0.18, h05 - 0.5 + r),
            vg.Point(r, h05 - 0.5 + r)
        ], [
            # -- Opponent Goal Area -- #
            vg.Point(self._field.fieldLength, h05 - 1),
            vg.Point(self._field.fieldLength, h05 + 1),
            vg.Point(self._field.fieldLength - 1, h05 + 1),
            vg.Point(self._field.fieldLength - 1, h05 - 1)
        ]]

        print("Control module started")

    def gen_triangles(self, center, radius) -> list[vg.Point]:
        # P1: [robot.x, 2 * radius + robot.y]
        # P2: [robot.x - (sin(60)  2 * radius), robot.y - radius]
        # P3: [robot.x + (sin(60)  2 * radius), robot.y - radius]

        return [
            vg.Point(center[0], 2 * radius + center[1]),
            vg.Point(center[0] - 1.7 * radius, center[1] - radius),
            vg.Point(center[0] + 1.7 * radius, center[1] - radius),
        ]

    def update(self):
        self.meta = self._coach.commands['meta']
        self.commands = self._coach.commands['robots']

        opposites_poly = [self.gen_triangles(r, .18 + 0.1) for r in self._match.opposites if not r.missing]
        self.vis_graph.build(self._field_poly + opposites_poly, workers=self._num_workers, status=False)

        all_paths = []

        for command in self.commands:
            if command.target_pose is None:
                continue

            points = self.vis_graph.shortest_path(
                vg.Point(command.robot.x, command.robot.y),
                vg.Point(command.target_pose[0], command.target_pose[1])
            )
            all_paths.append(points)
            next_point = points[1]

            if len(points) > 2 and distance_between_points(command.robot, [next_point.x, next_point.y]) < 0.05:
                next_point = points[2]

            dx = next_point.x - command.robot.x
            dy = next_point.y - command.robot.y

            dt = reduce_ang(command.target_pose[2] - command.robot.theta)

            command.move_speed = (dx * self.KP, dy * self.KP, dt * self.KP_ang)

        if time.time() - self.last_info > 0.1:
            self.last_info = time.time()
            paths = []
            for path in all_paths:
                paths.append(';'.join(f"%0.2f,%0.2f" % (point.x, point.y) for point in path))
            MESSAGE = 'a'.join(paths).encode('ascii')
            self.sock.sendto(MESSAGE, (self.UDP_IP, self.UDP_PORT))

        self.new_data = True
