from collections import deque
from math import sin, cos, pi

from commons.velocities import avg_angular_speed, avg_linear_speed

class OmniRobot():
    def __init__(self, game, team_color, robot_id) -> None:
        self.game = game
        self.robot_id = robot_id
        self.team_color = team_color

        self.strategy = None

        self.dimensions = {
            'L': 0.075,
            'R': 0.035
        }


        self.last_poses = {
            'x': deque(maxlen=10),
            'y': deque(maxlen=10),
            'theta': deque(maxlen=10)
        }

        self.vx, self.vy, self.vtheta = 0, 0, 0
        self.x, self.y, self.theta = 0, 0, 0

        self.speed = 0
        self.last_frame = 0
        self.actual_frame = 0

        self.current_data = None
        self.strategy = None

    def get_name(self):
        return 'SSLROBOT_{}_{}'.format(self.robot_id, self.team_color)

    def set_strategy(self, strategy_ref):
        self.strategy = strategy_ref(self)

        self.strategy.start()

    def get_robot_in_frame(self, frame):
        team_color_key = 'robotsBlue' if self.team_color == 'BLUE' else 'robotsYellow'

        if frame.get(team_color_key) is None:
            return None
        robot_data = frame[team_color_key].get(self.robot_id)
        return robot_data


    def get_speed(self):
        return (self.vx ** 2 + self.vy ** 2) ** .5

    def update_pose(self):
        self.last_poses['x'].append(self.current_data['x'])
        self.last_poses['y'].append(self.current_data['y'])
        self.last_poses['theta'].append(self.current_data['theta'])

        self.theta = self.current_data['theta']
        self.x = self.current_data['x']
        self.y = self.current_data['y']

        self.vx = avg_linear_speed(self.last_poses['x'], self.game.vision._fps)
        self.vy = avg_linear_speed(self.last_poses['y'], self.game.vision._fps)
        self.vtheta = avg_angular_speed(self.last_poses['theta'], self.game.vision._fps)

        self.speed = self.get_speed()

    def update(self, frame):
        self.current_data = self.get_robot_in_frame(frame)
        if self.current_data.get('tCapture') > 0:
            self.update_pose()

    def decide(self):
        desired = self.strategy.decide()

        self.motor_powers = self.global_speed_to_wheel_speed(*desired)
        return self.motor_powers, desired

    def global_speed_to_wheel_speed(self, vx, vy):
        R = self.dimensions['L']
        r = self.dimensions['R']
        theta = self.theta

        w1 = (-vx * sin(theta + pi/4) + vy * cos(theta + pi/4) + theta * R)/r
        w2 = (-vx * sin(theta + 3/4 * pi) + vy * cos(theta + 3/4 * pi) + theta * R)/r
        w3 = (-vx * sin(theta + 5/4 * pi) + vy * cos(theta + 5/4 * pi) + theta * R)/r
        w4 = (-vx * sin(theta + 7/4 * pi) + vy * cos(theta + 7/4 * pi) + theta * R)/r

        return (w1, w2, w3, w4)
        

