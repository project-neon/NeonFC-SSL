from neonfc_ssl.decision_layer.decision import RobotCommand
from base_skill import BaseSkill


class Wait(BaseSkill):
    def decide(self, data):
        return RobotCommand(
            id=self._robot_id,
            halt=False
        )
