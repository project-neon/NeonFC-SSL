import time

from vision.gr_sim_vision import GrSimVision
from match.ssl_match import SSLMatch
from comm.serial_comm import SerialComm
from referee.ssl_game_controller import SSLGameControllerReferee

class Game():
    def __init__(self) -> None:
        
        self.vision = GrSimVision(self)
        self.match = SSLMatch(self)
        self.comm = SerialComm()
        self.referee = SSLGameControllerReferee()

    
    def start(self):
        self.match.start()
        self.vision.start()
        self.comm.start()
        self.referee.start()


    def update(self, detection):
        self.match.update(detection)
        commands = self.match.decide()
        self.comm.send(commands)


game = Game()

game.start()

