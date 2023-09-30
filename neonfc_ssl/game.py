import time

from vision.gr_sim_vision import GrSimVision
from match.ssl_match import SSLMatch

class Game():
    def __init__(self) -> None:
        
        self.vision = GrSimVision(self)
        self.match = SSLMatch(self)

    
    def start(self):
        self.vision.start()


    def update(self, detection):
        self.match.update(detection)

        self.match.decide()

        self.comm.send()


game = Game()

game.start()

