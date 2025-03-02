from neonfc_ssl.decision_layer.decision import RobotCommand
from base_skill import BaseSkill


class MoveToPose(BaseSkill):
    def _start(self, target, avoid_area=True, avoid_allies=False, avoid_opponents=False):
        self.target = target

        self.avoid_area = avoid_area
        self.avoid_allies = avoid_allies
        self.avoid_opponents = avoid_opponents

    def decide(self, data):
        return RobotCommand(
            id=self._robot_id,
            halt=False,
            target_pose=self.target,
            avoid_area=self.avoid_area,
            avoid_allies=[r.id for r in data.robots if r.id != self._robot_id] if self.avoid_allies else [],
            avoid_opponents=[r.id for r in data.opposites] if self.avoid_opponents else []
        )

    def complete(self, data):
        robot = data.robots[self._robot_id]

        return (((robot.x - self.target[0]) ** 2 + (robot.y - self.target[1]) ** 2) ** .5) < 0.1
