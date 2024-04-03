import json
import socket
import struct
import logging
import threading

from protocols.grSim import ssl_vision_wrapper_pb2
from google.protobuf.json_format import MessageToJson

def get_config(config_file=None):
    if config_file:
        config = json.loads(open(config_file, 'r').read())
    else:
        config = json.loads(open('config.json', 'r').read())

    return config


class GrSimVision(threading.Thread):
    def __init__(self, game, config_file=None) -> None:
        super(GrSimVision, self).__init__()
        self.config = get_config(config_file)

        self.game = game

        self._fps = 60

        self.raw_detection = {
            'ball': {
                'x': 0,
                'y': 0,
                'tCapture': -1,
                'cCapture': -1
            },
            'robotsBlue': {
                i: {'x': None, 'y': None, 'theta': None, 'tCapture': -1} for i in range(0, 6)
            },
            'robotsYellow': {
                i: {'x': None, 'y': None, 'theta': None, 'tCapture': -1} for i in range(0, 6)
            },
            'meta': {
                'cameras': {
                    i: {'last_capture': -1} for i in range(0, 4)
                }
            }
        }

        self.vision_port = self.config['network']['vision_port']
        self.host = self.config['network']['multicast_ip']

        console_handler = logging.StreamHandler()
        log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        self.logger = logging.Logger("vision")
        console_handler.setFormatter(log_formatter)
        self.logger.addHandler(console_handler)

    
    def run(self) -> None:
        self.logger.info(f"Creating socket with address: {self.host} and port: {self.vision_port}")
        self.vision_sock = self._create_socket()
        self._wait_to_connect()
        self.logger.info(f"Connection completed!")

        while True:
            env = ssl_vision_wrapper_pb2.SSL_WrapperPacket()
            data = self.vision_sock.recv(2048)

            env.ParseFromString(data)
            last_frame = json.loads(MessageToJson(env))
            self.update_detection(last_frame)

            self.update_game()
    

    def update_detection(self, last_frame):
        frame = last_frame.get('detection')
        if not frame:
            # pacote de deteccao sem frame
            return

        t_capture = frame.get('tCapture')
        camera_id = frame.get('cameraId')
        self.update_camera_capture_number(camera_id, t_capture)

        balls = frame.get('balls', [])
        self.update_ball_detection(balls, camera_id)

        robots_blue = frame.get('robotsBlue')
        if robots_blue:
            for robot in robots_blue:
                self.update_robot_detection(robot, t_capture, camera_id, color='Blue')

        robots_yellow = frame.get('yellowBlue')
        if robots_yellow:
            for robot in robots_yellow:
                self.update_robot_detection(robot, t_capture, camera_id, color='Yellow')

    def update_camera_capture_number(self, camera_id, t_capture):
        last_camera_data = self.raw_detection['meta']['cameras'][camera_id]

        if last_camera_data['last_capture'] > t_capture:
            return

        self.raw_detection['meta']['cameras'][camera_id] = {
            'last_capture': t_capture
        }

    def update_ball_detection(self, balls, camera_id):
        if len(balls) > 0:
            ball = balls[0]
            self.raw_detection['ball'] = {
                'x': ball.get('x')/1000 + 9/2,
                'y': ball.get('y')/1000 + 6/2,
                'tCapture': ball.get('tCapture'),
                'cCapture': camera_id
            }


    def update_robot_detection(self, robot, _timestamp, camera_id, color='Blue'):
        robot_id = robot.get('robotId')
        last_robot_data = self.raw_detection[ 
            'robots' + color
         ][robot_id]
        

        if last_robot_data.get('tCapture') > _timestamp:
            return
        
        self.raw_detection[
            'robots' + color
         ][robot_id] = {
            'x': robot['x']/1000 + 9 / 2,
            'y': robot['y']/1000 + 6 / 2,
            'theta': robot['orientation'],
            'tCapture': _timestamp,
            'cCapture': camera_id
        }

    def update_game(self):
        self.game.update(self.raw_detection)

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
