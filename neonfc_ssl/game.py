import time

from vision.gr_sim_vision import GrSimVision
from match.ssl_match import SSLMatch
from comm.serial_comm import SerialComm
from comm.grsim_comm import GrComm
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

        if self.referee._referee_message:
            print(self.referee._referee_message.get('command'))
        if self.referee.can_play():  
            self.comm.send(commands)
        else:
            self.comm.freeze(commands)


game = Game()

game.start()

