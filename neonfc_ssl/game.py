from vision.gr_sim_vision import GrSimVision
from vision.auto_ref_vision import AutoRefVision
from match.ssl_match import SSLMatch
from coach import COACHES, BaseCoach
from comm.serial_comm import SerialComm
from comm.grsim_comm import GrComm
from referee.ssl_game_controller import SSLGameControllerReferee


class Game:
    def __init__(self) -> None:
        self.ssl_vison = GrSimVision(self)
        self.auto_ref = AutoRefVision(self)
        self.vision = self.auto_ref
        self.geometry = self.ssl_vison
        self.referee = SSLGameControllerReferee()
        self.match = SSLMatch(self)
        self.coach = COACHES["TestCoach"](self)
        self.comm = GrComm(self)

    def start(self):
        self.ssl_vison.start()
        self.auto_ref.start()
        self.referee.start()
        self.match.start()
        self.coach.start()
        self.comm.start()

        self.update()

    def update(self):
        while True:
            if self.vision.new_data:
                self.match.update()
                self.coach.update()
                self.comm.send()


game = Game()
game.start()
