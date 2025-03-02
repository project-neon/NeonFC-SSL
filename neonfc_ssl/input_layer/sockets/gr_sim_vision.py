import json
import socket
import struct
import logging
import threading
import math
from google.protobuf.json_format import MessageToJson
from neonfc_ssl.input_layer.input_data import Ball, Robot, Geometry, Entities
from neonfc_ssl.protocols.grSim import ssl_vision_wrapper_pb2


class GrSimVision(threading.Thread):
    def __init__(self, config, log) -> None:
        super(GrSimVision, self).__init__()

        self.config = config
        self.daemon = True

        self.running = False

        self._fps = 60
        self.new_data = False
        self.any_geometry = False

        self.raw_detection: Entities = Entities(None, {}, {})
        self.raw_geometry: Geometry = None

        self.side_factor = 1
        self.angle_factor = 0

        self.vision_port = self.config['network']['vision_port']
        self.host = self.config['network']['multicast_ip']

        self.logger = log

    def run(self):
        self.logger(logging.INFO, f"Starting SSL-Vision module...")
        self.logger(logging.INFO, f"Creating socket with address: {self.host} and port: {self.vision_port}")
        self.vision_sock = self._create_socket()
        self._wait_to_connect()
        self.logger(logging.INFO, f"SSL-Vision module started!")

        self.running = True
        while self.running:
            env = ssl_vision_wrapper_pb2.SSL_WrapperPacket()
            data = self.vision_sock.recv(2048)

            env.ParseFromString(data)

            last_frame = json.loads(MessageToJson(env))
            self.new_data = self.update_detection(last_frame) or self.new_data
        self.stop()

    def stop(self):
        self.running = False
        self.vision_sock.close()
        self.logger(logging.INFO, f"SSL-Vision module stopped!")

    def update_detection(self, last_frame):
        frame = last_frame.get('detection')
        if not frame:
            # pacote de deteccao sem frame
            return False

        t_capture = frame.get('tCapture')
        camera_id = frame.get('cameraId')

        self.side_factor = 1 if self.config['match']['team_side'] == 'left' else -1
        self.angle_factor = 0 if self.config['match']['team_side'] == 'left' else math.pi

        balls = frame.get('balls', [])
        self.update_ball_detection(balls, camera_id)

        robots_blue = frame.get('robotsBlue')
        if robots_blue:
            for robot in robots_blue:
                self.update_robot_detection(robot, t_capture, camera_id, color='blue')

        robots_yellow = frame.get('robotsYellow')
        if robots_yellow:
            for robot in robots_yellow:
                self.update_robot_detection(robot, t_capture, camera_id, color='yellow')

        geometry = last_frame.get('geometry')
        self.any_geometry = self.any_geometry or self.update_geometry(geometry)

        return True
    
    def update_geometry(self, frame):
        if not frame:
            # pacote de deteccao sem frame
            return False
        
        frame = frame.get('field')

        self.raw_geometry = Geometry(
            field_length=frame.get('fieldLength')/1000,
            field_width=frame.get('fieldWidth')/1000,
            goal_width=frame.get('goalWidth')/1000,
            penalty_depth=frame.get('penaltyAreaDepth', 1000)/1000,
            penalty_width=frame.get('penaltyAreaWidth', 2000)/1000
        )

        return True

    def update_ball_detection(self, balls, camera_id):
        if len(balls) < 1:
            return

        ball = balls[0]
        self.raw_detection.ball = Ball(
            x=self.side_factor*ball.get('x')/1000,
            y=self.side_factor*ball.get('y')/1000,
            timestamp=ball.get('tCapture'),
            camera_id=camera_id
        )

    def update_robot_detection(self, robot, _timestamp, camera_id, color='blue'):
        robot_id = robot.get('robotId')

        # last_robot_data = self.raw_detection[
        #     'robots' + color
        #  ][robot_id]
        #
        # if last_robot_data.get('tCapture') > _timestamp:
        #     return

        if color == 'blue':
            self.raw_detection.robots_blue[robot_id] = Robot(
                id=robot_id,
                team=color,
                x=self.side_factor*robot['x']/1000,
                y=self.side_factor*robot['x']/1000,
                theta=robot['orientation'] + self.angle_factor,
                timestamp=_timestamp,
                camera_id=camera_id
            )

        else:
            self.raw_detection.robots_yellow[robot_id] = Robot(
                id=robot_id,
                team=color,
                x=self.side_factor*robot['x']/1000,
                y=self.side_factor*robot['x']/1000,
                theta=robot['orientation'] + self.angle_factor,
                timestamp=_timestamp,
                camera_id=camera_id
            )

    def get_last_frame(self) -> Entities:
        self.new_data = False
        return self.raw_detection

    def get_geometry(self) -> Geometry:
        return self.raw_geometry

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
