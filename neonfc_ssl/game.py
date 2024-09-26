import json
import atexit
import logging.config
from vision.gr_sim_vision import GrSimVision
from vision.auto_ref_vision import AutoRefVision
from match.ssl_match import SSLMatch
from coach import COACHES, BaseCoach
from comm.serial_comm import SerialComm
from comm.grsim_comm import GrComm
from referee.ssl_game_controller import SSLGameControllerReferee
from control import Control


def get_config(config_file=None):
    if config_file:
        config = json.loads(open(config_file, 'r').read())
    else:
        config = json.loads(open('config.json', 'r').read())

    return config


class Game:
    def __init__(self) -> None:
        # Load Config
        self.config = get_config()
        self.match_name = "Test"
        self.t1 = self.config['match'].get('team_1', None)
        self.t2 = self.config['match'].get('team_2', None)
        self.event = self.config['match'].get('event', None)

        self.match_name = f"{self.t1}x{self.t2}@{self.event}" if self.t1 and self.t2 and self.event else "test"

        # Config Logger
        self.setup_logger()

        self.logger = logging.getLogger("game")

        # Input Layer
        self.ssl_vison = GrSimVision(self)
        self.auto_ref = AutoRefVision(self)
        self.referee = SSLGameControllerReferee()

        self.vision = self.auto_ref
        self.geometry = self.ssl_vison

        # Tracking Layer
        self.match = SSLMatch(self)

        # Decision Layer
        self.coach = COACHES["TestCoach"](self)

        # Control Layer
        self.control = Control(self)

        # Output Layer
        self.comm = GrComm(self)

        # Register exit handler
        atexit.register(self.stop_threads)

    def start(self):
        self.logger.info("Starting game")
        info = {"t1": self.t1, "t2": self.t2, "event": self.event, "vision": type(self.vision).__name__}
        self.logger.game("game begin", extra=info)
        info["coach"] = "TestCoach"
        self.logger.decision("game begin", extra=info)

        # Input Layer
        self.ssl_vison.start()
        self.auto_ref.start()
        self.referee.start()

        # Tracking Layer
        self.match.start()

        # Decision Layer
        self.coach.start()

        # Control Layer
        self.control.start()

        # Output Layer
        self.comm.start()

        self.update()

    def setup_logger(self):
        if (t1 := self.config['match'].get('team_1', None)) is not None and \
           (t2 := self.config['match'].get('team_2', None)) is not None and \
           (event := self.config['match'].get('event', None)) is not None:

            self.match_name = f"{t1}x{t2}@{event}"

        self.config['logger']['handlers']['file']['filename'] = f"logs/{self.match_name}.log.jsonl"
        logging.config.dictConfig(self.config['logger'])

    def stop_threads(self):
        self.ssl_vison.stop()
        self.auto_ref.stop()
        self.referee.stop()

    def update(self):
        while True:
            if self.vision.new_data:
                self.match.update()
                self.coach.update()
                self.control.update()
                self.comm.send()


game = Game()
game.start()
