from neonfc_ssl.strategies.base_strategy import BaseStrategy
from neonfc_ssl.skills import *
from math import atan2, tan, pi


class Libero(BaseStrategy):
    def __init__(self, coach, match, defensive_positions):
        super().__init__('Libero', coach, match)
        
        self.defensive_positions = defensive_positions
        self.field = self._match.field
        self.target = None

        self.states = {
            'move_to_pose': MoveToPose(coach, match)
        }

    def _start(self):
        self.active = self.states['move_to_pose']
        self.active.start(self._robot, target=self._defense_front)

    def decide(self):
        #print(self.defensive_positions)
        next = self.active.update()

        target = self._defense_front()
        self.active = next
        self.active.start(self._robot, target=target)

        return self.active.decide()
      
    def _defense_front(self):
        x = self.defensive_positions[self._robot.robot_id][0]
        y = self.defensive_positions[self._robot.robot_id][1]
        # print(f"robot_{self._robot.robot_id}: desired_y = {y}")
        theta = atan2(-self._robot.y + self._match.ball.y, -self._robot.x + self._match.ball.x)
        return [x, y, theta]