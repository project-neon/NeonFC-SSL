from neonfc_ssl.entities import OmniRobot, Ball
from neonfc_ssl.possession_tracker import PossessionTracker
from neonfc_ssl.state_controller import StateController


class SSLMatch:
    def __init__(self, game) -> None:
        self._game = game

        # Input Layer classes
        self._vision = None
        self._referee = None

        # Tracking Objects
        self.robots: list[OmniRobot] = None
        self.ball = None
        self.opposites: list[OmniRobot] = None
        self.game_state = None
        self.possession = None

        # Other Tracking Info
        self.goalkeeper_id = 0
        self.team_color = 'blue'
        self.opponent_color = 'yellow'
        self.team_side = 'left'

    def start(self):
        print("Starting match module starting ...")

        # Get Last Layer Classes
        self._vision = self._game.vision
        self._referee = self._game.referee

        # Create Layer
        self.ball = Ball()

        self.robots = [OmniRobot(self, self.team_color, i) for i in range(0, 6)]

        self.opposites = [
            # 0, 1, 2, 3, 4, 5 opposite robots
            OmniRobot(self, self.opponent_color, i) for i in range(0, 6)
        ]

        self.game_state = StateController(self)

        self.possession = PossessionTracker(self, self.game_state)

        print("Match module started")

    def update(self):
        frame = self._vision.get_last_frame()
        ref_command = self._referee.simplify()

        self.ball.update(frame)

        for robot in self.robots:
            robot.update(frame)

        for opposite in self.opposites:
            opposite.update(frame)

        self.game_state.update(ref_command)

        self.possession.update()
