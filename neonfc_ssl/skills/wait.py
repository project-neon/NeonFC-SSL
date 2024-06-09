from neonfc_ssl.skills.base_skill import BaseSkill
from neonfc_ssl.entities import RobotCommand
import random


class Wait(BaseSkill):
    def __init__(self, coach, match):
        super().__init__('Wait', coach, match)

    def decide(self):
        return RobotCommand(
            robot_id=self._robot.robot_id,
            spinner=True,
            move_speed=(0, 0, random.normalvariate(0, 0.2))
        )
