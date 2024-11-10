from socket import *
import json
import logging


class Api:
    def __init__(self, match, config):
        self._config = config
        self._address = None
        self._port = None
        self._socket: socket = None
        self._match = match

        self.started = False

        self._logger = logging.getLogger("api")

    # Initiate socket connection
    def start(self):
        self._socket = socket(AF_INET, SOCK_DGRAM)
        self._address = self._config['network'].get('host_ip', '0.0.0.0')
        self._port = self._config['network'].get('api_port')

        if self._port is None or self._address is None:
            self._logger.error("Unable to configure api, port not found")
            return

        self.started = True

    # Sends dict game data to socket listener
    def send_data(self):
        if not self.started:
            self._logger.warning("Trying to send data on api before start")
            return

        data_dict = self.parse_data()
        msg = json.dumps(data_dict)
        self._socket.sendto(msg.encode(), (self._address, self._port))

    def parse_data(self):
        rob = self._match.robots
        op = self._match.opposites
        ball = self._match.ball

        gen_rob_line = lambda r: [r.x, r.y, r.theta] if not r.missing else [-2, -2, r.theta]

        formated_data = {
            'TEAM_ROBOTS': {
                'ROBOT_POS': {f"{r.robot_id}": gen_rob_line(r) for r in rob},
                'STRATEGY': {f"{r.robot_id}": r.strategy.name for r in rob},
            }, 'OPPOSITE_ROBOTS': {
                'ROBOT_POS': {f"{r.robot_id}": gen_rob_line(r) for r in op}
            }, 'BALL': {
                'BALL_POS': [ball.x, ball.y]
            }
        }

        return formated_data
