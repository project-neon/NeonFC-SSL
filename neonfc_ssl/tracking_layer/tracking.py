import logging
from neonfc_ssl.core import Layer
from neonfc_ssl.core.logger import TRACKING
from .entities import OmniRobot, Ball, ball
from .possession_tracker import FloatPossessionTracker as PossessionTracker
from .state_controller import StateController
from .tracking_data import MatchData

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.input_layer.input_data import InputData


class Tracking(Layer):
    def __init__(self, config, log_q, event_pipe):
        super().__init__("TrackingLayer", config, log_q, event_pipe)

        if self.config['color'] != 'blue' and self.config['color'] != 'yellow':
            raise ValueError("color must be either 'blue' or 'yellow'")

        # Tracking Objects
        self.ball: Ball = None
        self.robots: list[OmniRobot] = None
        self.active_robots: list[OmniRobot] = None
        self.opposites: list[OmniRobot] = None
        self.active_opposites: list[OmniRobot] = None
        self.game_state: StateController = None
        self.possession: PossessionTracker = None

        # Other Tracking Parameters
        self.team_color = self.config['color']
        self.opponent_color = 'yellow' if self.config['color'] == 'blue' else 'blue'

    def _start(self):
        self.logger.info("Starting match module starting ...")

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
        out_data = MatchData(
            robots=[r.data for r in self.robots],
            opposites=[r.data for r in self.opposites],
            ball=self.ball.data,
            possession=poss,
            game_state=state,
            field=geometry,
            is_yellow=self.team_color=='yellow'
        )
        self.logger.log(TRACKING, out_data)
        return out_data
