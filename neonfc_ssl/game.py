import json
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

    def start(self):
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

    def update(self):
        while True:
            if self.vision.new_data:
                self.match.update()
                self.coach.update()
                self.control.update()
                self.comm.send()


game = Game()
game.start()
