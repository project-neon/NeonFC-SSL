import logging
from neonfc_ssl.entities import OmniRobot, Ball, Field
from neonfc_ssl.possession_tracker import FloatPossessionTracker as PossessionTracker
from neonfc_ssl.state_controller import StateController
from neonfc_ssl.api import Api


class SSLMatch:
    def __init__(self, game) -> None:
        self._game = game

        # Input Layer classes
        self._geometry = None
        self._vision = None
        self._referee = None

        # Tracking Objects
        self.ball: Ball = None
        self.field: Field = None
        self.robots: list[OmniRobot] = None
        self.active_robots: list[OmniRobot] = None
        self.opposites: list[OmniRobot] = None
        self.active_opposites: list[OmniRobot] = None
        self.game_state: StateController = None
        self.possession: PossessionTracker = None

        # Other Tracking Parameters
        self.goalkeeper_id = 0
        self.team_color = self._game.config['match']['team_color']
        self.opponent_color = 'yellow' if self._game.config['match']['team_color'] == 'blue' else 'blue'

        self.api: Api = None

        self.logger = logging.getLogger("match")

    def start(self):
        self.logger.info("Starting match module starting ...")

        # Get Last Layer Classes
        self._geometry = self._game.geometry
        self._vision = self._game.vision
        self._referee = self._game.referee

        # Create Layer
        self.ball = Ball()

        self.robots = [
            OmniRobot(self, self.team_color, i) for i in range(0, 16)
        ]

        self.field = Field()

        self.active_robots = self.robots

        self.opposites = [
            # 0, 1, 2, 3, 4, 5 opposite robots
            OmniRobot(self, self.opponent_color, i) for i in range(0, 16)
        ]

        self.active_opposites = self.opposites

        self.game_state = StateController(self)

        self.possession = PossessionTracker(self, self.game_state)

        self.api = Api(self, self._game.config)
        self.api.start()

        self.logger.info("Match module started!")

    def update(self):
        frame = self._vision.get_last_frame()
        geometry = self._geometry.get_geometry()

        ref_command = self._referee.simplify()

        self.field.update(geometry)

        self.ball.update(frame, self.field)
        extra = {'ball': [
            round(self.ball.x, 3), round(self.ball.y, 3),
            round(self.ball.vx, 3), round(self.ball.vy, 3)
        ], 'b': {}, 'y': {}}

        for robot in self.robots:
            robot.update(frame, self.field)
            extra[robot.team_color[0]][robot.robot_id] = [
                int(robot.missing),
                round(robot.x, 3), round(robot.y, 3), round(robot.theta, 3),
                round(robot.vx, 3), round(robot.vy, 3), round(robot.vtheta, 3)
            ]

        self.active_robots = [r for r in self.robots if not r.missing]

        for opposite in self.opposites:
            opposite.update(frame, self.field)
            extra[opposite.team_color[0]][opposite.robot_id] = [
                int(opposite.missing),
                round(opposite.x, 3), round(opposite.y, 3), round(opposite.theta, 3),
                round(opposite.vx, 3), round(opposite.vy, 3), round(opposite.vtheta, 3)
            ]

        self.active_opposites = [r for r in self.opposites if not r.missing]

        self.logger.game("frame", extra=extra)

        self.api.send_data()

        self.game_state.update(ref_command)

        self.possession.update()
