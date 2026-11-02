import torch
from typing import TYPE_CHECKING
from ..drl_commons import STRIKER_ID, GOALKEEPER_ID
from .transformation_registry import transformation_registry

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData, TrackedRobot


def _get_robot_features(robot: "TrackedRobot") -> list[float]:
    if robot is None or robot.missing:
        return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    return [robot.x, robot.y, robot.theta, robot.vx, robot.vy, robot.vtheta]


@transformation_registry.register("n_robots")
def input_transformation(ids: list[int], data: "MatchData") -> torch.Tensor:
    features = []
    for rid in ids:
        features.extend(_get_robot_features(data.robots[rid]))
    ball = data.ball
    features.extend([ball.x, ball.y, ball.vx, ball.vy])
    return torch.tensor(features, dtype=torch.float32)
