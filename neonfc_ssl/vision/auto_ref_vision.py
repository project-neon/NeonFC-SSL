import json
import socket
import struct
import logging
import threading
import math
from google.protobuf.json_format import MessageToJson

from neonfc_ssl.protocols.gc.ssl_vision_wrapper_tracked_pb2 import TrackerWrapperPacket


class AutoRefVision(threading.Thread):
    def __init__(self, game, config_file=None) -> None:
        super(AutoRefVision, self).__init__()

        self.game = game
        self.config = self.game.config

        self.running = False

        self._fps = 60
        self.new_data = False

        self.raw_detection = {
            'ball': {
                'x': 0.0,
                'y': 0.0,
                'z': 0.0,
                'vx': 0.0,
                'vy': 0.0,
                'vz': 0.0,
                'tCapture': -1
            },
            'robotsBlue': {
                i: {
                    'x': None, 'y': None, 'theta': None,
                    'vx': None, 'vy': None, 'w': None,
                    'tCapture': -1
                } for i in range(0, 6)
            },
            'robotsYellow': {
                i: {
                    'x': None, 'y': None, 'theta': None,
                    'vx': None, 'vy': None, 'w': None,
                    'tCapture': -1
                } for i in range(0, 6)
            },
            'meta': {
                'has_speed': True,
                'has_height': True,
                'cameras': {
                    i: {'last_capture': -1} for i in range(0, 4)
                }
            }
        }

        self.side_factor = 1
        self.angle_factor = 0

        self.vision_port = self.config['network']['autoref_port']
        self.host = self.config['network']['multicast_ip']

        self.logger = logging.getLogger("input")

    def run(self):
        self.logger.info(f"Starting AutoRef-Vision module...")
        self.logger.info(f"Creating socket with address: {self.host} and port: {self.vision_port}")
        self.vision_sock = self._create_socket()
        self._wait_to_connect()
        self.logger.info(f"AutoRef-Vision module started!")

        self.running = True
        while self.running:
            env = TrackerWrapperPacket()
            data = self.vision_sock.recv(2048)
            env.ParseFromString(data)
            last_frame = json.loads(MessageToJson(env))
            self.new_data = self.update_detection(last_frame)

        self.logger.info(f"AutoRef-Vision module stopped!")

    def stop(self):
        self.running = False

    def update_detection(self, last_frame):
        frame = last_frame.get('trackedFrame', None)
        if not frame:
            # pacote de deteccao sem frame
            return False
        t_capture = frame.get('timestamp')

        self.side_factor = 1 if self.config['match']['team_side'] == 'left' else -1
        self.angle_factor = 0 if self.config['match']['team_side'] == 'left' else math.pi

        balls = frame.get('balls', [])
        self.update_ball_detection(balls, t_capture)

        robots = frame.get('robots')
        if robots:
            for robot in robots:
                self.update_robot_detection(robot, t_capture)

        robots_yellow = frame.get('robotsYellow')
        if robots_yellow:
            for robot in robots_yellow:
                self.update_robot_detection(robot, t_capture)

        return True

    def update_camera_capture_number(self, camera_id, t_capture):
        last_camera_data = self.raw_detection['meta']['cameras'][camera_id]

        if last_camera_data['last_capture'] > t_capture:
            return

        self.raw_detection['meta']['cameras'][camera_id] = {
            'last_capture': t_capture
        }

    def update_ball_detection(self, balls, _timestamp):
        if len(balls) > 0:
            pos = balls[0]['pos']
            speed = balls[0]['vel']
            self.raw_detection['ball'] = {
                'x': self.side_factor*pos['x'] + 9/2,
                'y': self.side_factor*pos['y'] + 6/2,
                'z': pos['z'],
                'vx': self.side_factor*speed['x'],
                'vy': self.side_factor*speed['y'],
                'vz': speed['z'],
                'tCapture': _timestamp
            }

    def update_robot_detection(self, robot, _timestamp):
        robot_id = robot['robotId']['id']
        color = 'Blue' if robot['robotId']['team'] == 'BLUE' else 'Yellow'
        pos = robot['pos']
        speed = robot['vel']
        last_robot_data = self.raw_detection['robots' + color][robot_id]

        # if last_robot_data.get('tCapture') > _timestamp:
        #     return

        self.raw_detection['robots' + color][robot_id] = {
            'x': self.side_factor*pos['x'] + 9/2,
            'y': self.side_factor*pos['y'] + 6/2,
            'theta': robot['orientation'] + self.angle_factor,
            'vx': self.side_factor*speed['x'],
            'vy': self.side_factor*speed['y'],
            'vt': robot['velAngular'],
            'tCapture': _timestamp
        }

    def get_last_frame(self):
        self.new_data = False
        return self.raw_detection

    def _wait_to_connect(self):
        self.vision_sock.recv(1024)

    def _create_socket(self):
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )

        sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )

        sock.bind((self.host, self.vision_port))

        mreq = struct.pack(
            "4sl", socket.inet_aton(self.host), socket.INADDR_ANY
        )

        sock.setsockopt(
            socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq
        )

        return sock
