import json
import socket
import struct
import logging
import threading
import math
from google.protobuf.json_format import MessageToJson
from neonfc_ssl.protocols.grSim import ssl_vision_wrapper_pb2


class GrSimVision(threading.Thread):
    def __init__(self, game) -> None:
        super(GrSimVision, self).__init__()

        self.game = game
        self.config = self.game.config
        self.daemon = True

        self.running = False

        self._fps = 60
        self.new_data = False
        self.any_geometry = False

        self.raw_geometry = {
            'fieldLength': 0,
            'fieldWidth': 0,
            'goalWidth': 0,
            'fieldLines': {
                'LeftGoalLine':{
                    'p1': {
                        'x': 0,
                        'y': 0
                    }
                },
                'RightGoalLine':{
                    'p1': {
                        'x': 0,
                        'y': 0,
                    }
                },
                'HalfwayLine':{
                    'p1':{
                        'x': 0,
                        'y': 0
                    }
                },
                'LeftPenaltyStretch':{
                    'p1':{
                        'x': 0,
                        'y': 0
                    }
                },
                'RightPenaltyStretch':{
                    'p1':{
                        'x': 0,
                        'y': 0
                    }
                },
                'RightGoalBottomLine':{
                    'p1':{
                        'x': 0,
                        'y': 0
                    }
                },
                'LeftGoalBottomLine':{
                    'p1':{
                        'x': 0,
                        'y': 0
                    }
                }
            }
        }

        self.raw_detection = {
            'ball': {
                'x': 0,
                'y': 0,
                'tCapture': -1,
                'cCapture': -1
            },
            'robotsBlue': {
                i: {'x': None, 'y': None, 'theta': None, 'tCapture': -1} for i in range(0, 16)
            },
            'robotsYellow': {
                i: {'x': None, 'y': None, 'theta': None, 'tCapture': -1} for i in range(0, 16)
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

        self.vision_port = self.config['network']['vision_port']
        self.host = self.config['network']['multicast_ip']

        self.logger = logging.getLogger("input")

    def run(self):
        self.logger.info(f"Starting SSL-Vision module...")
        self.logger.info(f"Creating socket with address: {self.host} and port: {self.vision_port}")
        self.vision_sock = self._create_socket()
        self._wait_to_connect()
        self.logger.info(f"SSL-Vision module started!")

        self.running = True
        while self.running:
            env = ssl_vision_wrapper_pb2.SSL_WrapperPacket()
            data = self.vision_sock.recv(2048)

            env.ParseFromString(data)
        
            last_frame = json.loads(MessageToJson(env))
            self.new_data = self.update_detection(last_frame)
            self.new_geometry = self.update_geometry(last_frame)
        self.stop()

    def stop(self):
        self.running = False
        self.vision_sock.close()
        self.logger.info(f"SSL-Vision module stopped!")

    def update_detection(self, last_frame):
        frame = last_frame.get('detection')
        if not frame:
            # pacote de deteccao sem frame
            return False

        t_capture = frame.get('tCapture')
        camera_id = frame.get('cameraId')
        self.update_camera_capture_number(camera_id, t_capture)

        self.side_factor = 1 if self.config['match']['team_side'] == 'left' else -1
        self.angle_factor = 0 if self.config['match']['team_side'] == 'left' else math.pi

        balls = frame.get('balls', [])
        self.update_ball_detection(balls, camera_id)

        robots_blue = frame.get('robotsBlue')
        if robots_blue:
            for robot in robots_blue:
                self.update_robot_detection(robot, t_capture, camera_id, color='Blue')

        robots_yellow = frame.get('robotsYellow')
        if robots_yellow:
            for robot in robots_yellow:
                self.update_robot_detection(robot, t_capture, camera_id, color='Yellow')

        return True
    
    def update_geometry(self, last_frame):
        frame = last_frame.get('geometry')

        if not frame:
            # pacote de deteccao sem frame
            return False
        self.any_geometry = True
        
        frame = frame.get('field')

        self.raw_geometry['fieldLength'] = frame.get('fieldLength')/1000
        self.raw_geometry['fieldWidth'] = frame.get('fieldWidth')/1000
        self.raw_geometry['goalWidth'] = frame.get('goalWidth')/1000
        self.raw_geometry['penaltyAreaDepth'] = frame.get('penaltyAreaDepth')/1000
        self.raw_geometry['penaltyAreaWidth'] = frame.get('penaltyAreaWidth')/1000

        self.raw_geometry['fieldLines']['LeftGoalLine']['p1']['x'] = (frame.get('fieldLines')[2].get('p1').get('x')/1000)
        self.raw_geometry['fieldLines']['RightGoalLine']['p1']['x'] = (frame.get('fieldLines')[3].get('p1').get('x')/1000)
        self.raw_geometry['fieldLines']['HalfwayLine']['p1']['x'] = (frame.get('fieldLines')[4].get('p1').get('x')/1000)
        self.raw_geometry['fieldLines']['LeftPenaltyStretch']['p1']['x'] = (frame.get('fieldLines')[6].get('p1').get('x')/1000)
        self.raw_geometry['fieldLines']['RightPenaltyStretch']['p1']['x'] = (frame.get('fieldLines')[7].get('p1').get('x')/1000)
        self.raw_geometry['fieldLines']['RightGoalBottomLine']['p1']['x'] = (frame.get('fieldLines')[9].get('p1').get('x')/1000)
        # self.raw_geometry['fieldLines']['LeftGoalBottomLine']['p1']['x'] = (frame.get('fieldLines')[12].get('p1').get('x')/1000)

        self.raw_geometry['fieldLines']['LeftGoalLine']['p1']['y'] = (frame.get('fieldLines')[2].get('p1').get('y')/1000)
        self.raw_geometry['fieldLines']['RightGoalLine']['p1']['y'] = (frame.get('fieldLines')[3].get('p1').get('y')/1000)
        self.raw_geometry['fieldLines']['HalfwayLine']['p1']['y'] = (frame.get('fieldLines')[4].get('p1').get('y')/1000)
        self.raw_geometry['fieldLines']['LeftPenaltyStretch']['p1']['y'] = (frame.get('fieldLines')[6].get('p1').get('y')/1000)
        self.raw_geometry['fieldLines']['RightPenaltyStretch']['p1']['y'] = (frame.get('fieldLines')[7].get('p1').get('y')/1000)
        self.raw_geometry['fieldLines']['RightGoalBottomLine']['p1']['y'] = (frame.get('fieldLines')[9].get('p1').get('y')/1000)
        # self.raw_geometry['fieldLines']['LeftGoalBottomLine']['p1']['y'] = (frame.get('fieldLines')[12].get('p1').get('y')/1000)

        return True

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
                'x': self.side_factor * ball.get('x')/1000,
                'y': self.side_factor * ball.get('y')/1000,
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
            'x': self.side_factor * robot['x']/1000,
            'y': self.side_factor * robot['y']/1000,
            'theta': robot['orientation'] + self.angle_factor,
            'tCapture': _timestamp,
            'cCapture': camera_id
        }
    
    def get_geometry(self):
        self.new_data = False
        return self.raw_geometry

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
