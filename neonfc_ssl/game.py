from vision.gr_sim_vision import GrSimVision
from vision.auto_ref_vision import AutoRefVision
from match.ssl_match import SSLMatch
from coach import COACHES, BaseCoach
from comm.serial_comm import SerialComm
from comm.grsim_comm import GrComm
from referee.ssl_game_controller import SSLGameControllerReferee


class Game:
    def __init__(self) -> None:
        self.vision1 = GrSimVision(self)
        self.vision2 = AutoRefVision(self)
        self.referee = SSLGameControllerReferee()
        self.match = SSLMatch(self)
        self.coach = COACHES["TestCoach"](self)
        self.comm = GrComm(self)

    def start(self):
        self.vision1.start()
        self.vision2.start()
        self.referee.start()
        self.match.start()
        self.coach.start()
        self.comm.start()

        self.update()

    def update(self):
        while True:
            if self.vision2.new_data:
                self.match.update()
                self.coach.update()
                self.comm.send()


game = Game()
game.start()
