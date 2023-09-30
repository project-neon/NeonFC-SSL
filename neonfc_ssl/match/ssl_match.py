

from html import entities


class SSLMatch():
    def __init__(self, game) -> None:
        
        self.game = game
        self.vision = game.vision

        self.team_color =   'BLUE'
        self.team_side  =   'LEFT'

    
    def start(self):
        print("Starting match module starting ...")
        self.ball = entities.Ball(self.game)

        self.goalkeeper = entities.Robot(self.game, self.team_color, 0)

        self.opposites = [
            # 0, 1, 2, 3, 4, 5 opposite robots
            entities.Robot(self.game, self.team_color, i) for i in range(0, 6)
        ]
    
    def update(self, frame):
        self.ball.update(frame)

        self.goalkeeper.update(frame)

        for opposite in self.opposites:
            opposite.update(frame)

    def decide(self):

        command = self.goalkeeper.decide()

        return command
