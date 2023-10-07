import time

from vision.gr_sim_vision import GrSimVision
from match.ssl_match import SSLMatch
from comm.grsim_comm import GrComm

class Game():
    def __init__(self) -> None:
        
        self.vision = GrSimVision(self)
        self.match = SSLMatch(self)
        self.comm = GrComm()

    
    def start(self):
        self.vision.start()
        self.match.start()
        self.comm.start()


    def update(self, detection):
        self.match.update(detection)
        commands = self.match.decide()

        self.comm.send(commands)


game = Game()

game.start()

