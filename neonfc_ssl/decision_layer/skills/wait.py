import time
from neonfc_ssl.decision_layer.decision import RobotRubric
from .base_skill import BaseSkill


class Wait(BaseSkill):
    def __init__(self, logger, strategy_name, duration=None):
        BaseSkill.__init__(self, logger, strategy_name)
        self.duration = None

    def _start(self, **kwargs):
        self.started_at = time.time()

    def decide(self, data):
        return RobotRubric.still(
            id=self._robot_id
        )

    def stop_waiting(self, *args, **kwargs):
        if self.duration is None:
            return True

        return time.time() - self.started_at >= self.duration
