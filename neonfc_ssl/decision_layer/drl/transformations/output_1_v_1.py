import torch
from typing import TYPE_CHECKING
from ..drl_commons import STRIKER_ID, GOALKEEPER_ID
from .transformation_registry import transformation_registry
from neonfc_ssl.decision_layer.decision_data import RobotRubric

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData

SHOOT_THRESHOLD = 0.5


def one_v_one_output_factory(goalkeeper_id: int, striker_id: int):
    model_to_robot_id = {
        "goalkeeper": goalkeeper_id,
        "striker": striker_id,
    }

    def output_transformation(actions: dict[str, torch.Tensor], match_data: "MatchData") -> dict[RobotRubric]:
        commands = {}
        for model_name, tensor in actions.items():
            robot_id = model_to_robot_id[model_name]
            x, y, theta, shooting_vx = tensor.tolist()
            kick_speed = (shooting_vx, 0.0) if shooting_vx > SHOOT_THRESHOLD else (0.0, 0.0)
            commands[robot_id] = RobotRubric(
                id=robot_id,
                halt=False,
                target_pose=(x, y, theta),
                kick_speed=kick_speed,
            )

        return commands

    return output_transformation


@transformation_registry.register("one_v_one_output")
def one_v_one_output_transformation(actions: dict[str, torch.Tensor], match_data: "MatchData") -> dict[RobotRubric]:
    return one_v_one_output_factory(GOALKEEPER_ID, STRIKER_ID)(actions, match_data)