from vision.gr_sim_vision import GrSimVision
from match.ssl_match import SSLMatch
from coach import COACHES, BaseCoach
from comm.serial_comm import SerialComm
from comm.grsim_comm import GrComm
from referee.ssl_game_controller import SSLGameControllerReferee


class Game:
    def __init__(self) -> None:
        self.vision = GrSimVision(self)
        self.referee = SSLGameControllerReferee()
        self.match = SSLMatch(self)
        self.coach = COACHES["TestCoach"](self)
        self.comm = GrComm(self)

    def start(self):
        self.vision.start()
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
