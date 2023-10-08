from entities.robot import OmniRobot
from entities.ball import Ball

from strategies.follow_ball import FollowBall
from strategies.goalkeeper import GoalKeeper


class SSLMatch():
    def __init__(self, game) -> None:
        
        self.game = game
        self.vision = game.vision

        self.goalkeeper_id  = 0
        self.team_color     =   'BLUE'
        self.opponent_color =   'YELLOW'
        self.team_side      =   'LEFT'

    
    def start(self):
        print("Starting match module starting ...")
        self.ball = Ball(self.game)

        self.goalkeeper = OmniRobot(self.game, self.team_color, self.goalkeeper_id)

        self.goalkeeper.set_strategy(GoalKeeper)


        self.opposites = [
            # 0, 1, 2, 3, 4, 5 opposite robots
            OmniRobot(self.game, self.opponent_color, i) for i in range(0, 6)
        ]
        print("Finish match module")
    
    def update(self, frame):
        self.ball.update(frame)

        self.goalkeeper.update(frame)

        for opposite in self.opposites:
            opposite.update(frame)

    def decide(self):

        results = self.goalkeeper.decide()
        command = results[0]
        desired = results[1]

        return [{
            'robot_id': self.goalkeeper.robot_id,
            'color': self.goalkeeper.team_color,
            'wheel_1': command[0],
            'wheel_2': command[1],
            'wheel_3': command[2],
            'wheel_4': command[3],
            'vx': desired[0],
            'vy': desired[1],
            'actual_theta': self.goalkeeper.theta,
            'can_kick': 0
        }]
