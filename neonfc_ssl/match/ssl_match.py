import logging
from neonfc_ssl.entities import OmniRobot, Ball
from neonfc_ssl.possession_tracker import FloatPossessionTracker as PossessionTracker
from neonfc_ssl.state_controller import StateController
from neonfc_ssl.api import Api
from neonfc_ssl.core import Layer
from neonfc_ssl.match.match_data import MatchData

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.input_l.input_data import InputData


class SSLMatch(Layer):
    def __init__(self, config, log_q, event_pipe):
        super().__init__("MatchLayer", config, log_q, event_pipe)

        self._previous_layer = "InputLayer"

        # Tracking Objects
        self.ball: Ball = None
        self.robots: list[OmniRobot] = None
        self.active_robots: list[OmniRobot] = None
        self.opposites: list[OmniRobot] = None
        self.active_opposites: list[OmniRobot] = None
        self.game_state: StateController = None
        self.possession: PossessionTracker = None

        # Other Tracking Parameters
        self.goalkeeper_id = 0
        self.team_color = self.config['match']['team_color']
        self.opponent_color = 'yellow' if self.config['match']['team_color'] == 'blue' else 'blue'

        self.logger = logging.getLogger("match")

    def _start(self):
        self.log(logging.INFO, "Starting match module starting ...")

        # Create Layer
        self.ball = Ball(self)

        self.robots = [
            OmniRobot(self, self.team_color, i) for i in range(0, 16)
        ]

        self.active_robots = self.robots

        self.opposites = [
            # 0, 1, 2, 3, 4, 5 opposite robots
            OmniRobot(self, self.opponent_color, i) for i in range(0, 16)
        ]

        self.active_opposites = self.opposites

        self.game_state = StateController(self)

        self.possession = PossessionTracker(self, self.game_state)

        self.logger.info("Match module started!")

    def _step(self, data: 'InputData'):
        geometry = data.geometry

        self.ball.update(data.entities.ball, data.geometry)

        rob, opp = (data.entities.robots_blue, data.entities.robots_yellow) if self.team_color == 'blue' else (data.entities.robots_yellow, data.entities.robots_blue)
        for robot in self.robots:
            robot.update(rob, data.geometry)

        self.active_robots = [r for r in self.robots if not r.data.missing]

        for opposite in self.opposites:
            opposite.update(opp, data.geometry)

        self.active_opposites = [r for r in self.opposites if not r.data.missing]

        state = self.game_state.update(data.game_controller)

        poss = self.possession.update()

        return MatchData(
            robots=[r.data for r in self.robots],
            opposites=[r.data for r in self.opposites],
            ball=self.ball.data,
            possession=poss,
            game_state=state,
            field=geometry
        )