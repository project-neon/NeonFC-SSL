from neonfc_ssl.decision_layer.decision import RobotRubric
from .base_skill import BaseSkill


class Wait(BaseSkill):
    def decide(self, data):
        return RobotRubric.still(
            id=self._robot_id
        )
