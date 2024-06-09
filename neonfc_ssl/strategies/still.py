from neonfc_ssl.strategies.base_strategy import BaseStrategy
from neonfc_ssl.entities import RobotCommand


class Still(BaseStrategy):
    def __init__(self, coach, match):
        super().__init__('Still', coach, match)

    def decide(self):
        return RobotCommand(robot_id=self._robot.robot_id)
