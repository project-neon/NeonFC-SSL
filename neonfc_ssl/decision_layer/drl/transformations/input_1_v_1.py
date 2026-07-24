import torch
from typing import TYPE_CHECKING
from ..drl_commons import STRIKER_ID, GOALKEEPER_ID
from .transformation_registry import transformation_registry

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData, TrackedRobot


def one_v_one_factory(goalkeeper_id: int, striker_id: int, device: str = "cpu"):
    def _get_robot_features(robot: "TrackedRobot") -> list[float]:
        if robot is None or robot.missing:
            return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        return [robot.x, robot.y, robot.theta, robot.vx, robot.vy, robot.vtheta]

    def input_transformation(data: "MatchData") -> torch.Tensor:
        features = []
        features.extend(_get_robot_features(data.robots[goalkeeper_id]))
        features.extend(_get_robot_features(data.robots[striker_id]))
        ball = data.ball
        features.extend([ball.x, ball.y, ball.vx, ball.vy])
        return torch.tensor(features, dtype=torch.float32, device=device)

    return input_transformation


@transformation_registry.register("one_v_one")
def one_v_one_transformation(data: "MatchData") -> torch.Tensor:
    return one_v_one_factory(GOALKEEPER_ID, STRIKER_ID)(data)
