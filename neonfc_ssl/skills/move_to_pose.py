from neonfc_ssl.entities import RobotCommand
from neonfc_ssl.skills.base_skill import BaseSkill


class MoveToPose(BaseSkill):
    def __init__(self, coach, match):
        super().__init__('MoveToPose', coach, match)

    def _start(self, target):
        self.target = target

    def decide(self):
        return RobotCommand(target_pose=self.target, robot=self._robot)

    def complete(self):
        return (((self._robot.x - self.target[0]) ** 2 + (self._robot.y - self.target[1]) ** 2) ** .5) < 0.1
