from neonfc_ssl.skills import *
from neonfc_ssl.strategies.base_strategy import BaseStrategy
from math import atan2


class BallPlacement(BaseStrategy):
    def __init__(self, name, coach, match):
        super().__init__('Kickoff', coach, match)
        self.name = name
        self._match = match
        self._coach = coach
        self._robot = None

        self.states = {
            'wait': Wait(coach, match),
            'move_to_pose': MoveToPose(coach, match)
        }

        self.states['wait'].add_transition(self.states['move_to_pose'])

    def _start(self):
        self.active = self.states['Wait']
        self.active.start(self._robot)
        
    def decide(self):
        next = self.active.update()
        target = self.position
        self.active = next
        self.active.start(self._robot, target=target)

        return self.active.decide()

    def position(self):
        field = self._match.field
        color = self._match.game_state.current_state.color
        foul_pos = self._match.game_state.current_state.position

        if color == self._match.opponent_color:
            if foul_pos[0] < field.fieldWidth/2:
                x = foul_pos[0] - 0.7
                y = foul_pos[1] + 0.7
            
            else:
                x = foul_pos[0] - 0.7
                y = foul_pos[1] - 0.7
        
        else:
            #testar escanteio (recebe freekick ou corner?)
            x = foul_pos[0] - 0.3 
            y = foul_pos[1] 

        theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)
        
        return [x, y, theta]
    
    def move_to_pose_transition(self):
        return True