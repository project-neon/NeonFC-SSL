import json
import socket
import struct
import logging
import threading
import math
from google.protobuf.json_format import MessageToJson
from neonfc_ssl.protocols.gc.ssl_vision_wrapper_tracked_pb2 import TrackerWrapperPacket
from ..input_data import Ball, Robot, Entities


class AutoRefVision(threading.Thread):
    def __init__(self, config, log) -> None:
        super(AutoRefVision, self).__init__(daemon=True)

        self.config = config

        self.running = False

        self._fps = 60
        self.new_data = False

        self.raw_detection: Entities = Entities(None, {}, {})
        self.side_factor = 1
        self.angle_factor = 0

        self.vision_port = self.config['autoref_port']
        self.host = self.config['multicast_ip']

        self.logger = log

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
            self.new_data = self.update_detection(last_frame) or self.new_data
        self.stop()

    def stop(self):
        self.running = False
        self.vision_sock.close()
        self.logger.info(f"AutoRef-Vision module stopped!")

    def update_detection(self, last_frame):
        # print(last_frame)
        # if last_frame.get("uuid") != "odvppkjjmzivzjfewcoeflgwbiuazobk":
        #     return

        frame = last_frame.get('trackedFrame', None)
        if not frame:
            # pacote de deteccao sem frame
            return False
        t_capture = frame.get('timestamp')

        # TODO: this should be done in tracking not in input
        self.side_factor = 1 if self.config['side'] == 'left' else -1
        self.angle_factor = 0 if self.config['side'] == 'left' else math.pi

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

    def update_ball_detection(self, balls, _timestamp):
        if len(balls) < 1:
            return

        ball = balls[0]
        pos = ball['pos']
        speed = ball['vel']
        self.raw_detection.ball = Ball(
            x=self.side_factor*pos['x'],
            y=self.side_factor*pos['y'],
            z=pos['z'],
            vx=self.side_factor*speed['x'],
            vy=self.side_factor*speed['y'],
            vz=speed['z'],
            timestamp=_timestamp
        )

    def update_robot_detection(self, robot, _timestamp):
        robot_id = robot['robotId']['id']
        color = 'blue' if robot['robotId']['team'] == 'BLUE' else 'yellow'
        pos = robot['pos']
        speed = robot['vel']

        # last_robot_data = self.raw_detection[color][robot_id]
        # if last_robot_data.get('tCapture') > _timestamp:
        #     return

        if color == 'blue':
            self.raw_detection.robots_blue[robot_id] = Robot(
                id=robot_id,
                team=color,
                x=self.side_factor*pos['x'],
                y=self.side_factor*pos['y'],
                theta=robot['orientation'] + self.angle_factor,
                vx=self.side_factor*speed['x'],
                vy=self.side_factor*speed['y'],
                vtheta=robot['velAngular'],
                timestamp=_timestamp
            )

        else:
            self.raw_detection.robots_yellow[robot_id] = Robot(
                id=robot_id,
                team=color,
                x=self.side_factor*pos['x'],
                y=self.side_factor*pos['y'],
                theta=robot['orientation'] + self.angle_factor,
                vx=self.side_factor*speed['x'],
                vy=self.side_factor*speed['y'],
                vtheta=robot['velAngular'],
                timestamp=_timestamp
            )

    def get_last_frame(self) -> Entities:
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
