from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neonfc_ssl.decision_layer.decision_data import RobotRubric
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class DRLStrategy:
    def __init__(self):
        self.last_decision = None

    def start(self, robot_id: int, *args, **kwargs):
        pass

    def inject_decision(self, decision: "RobotRubric"):
        self.last_decision = decision

    def decide(self, data: "MatchData") -> "RobotRubric":
        return self.last_decision