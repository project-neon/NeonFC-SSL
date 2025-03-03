from dataclasses import dataclass, field
from typing import Tuple, Optional
from neonfc_ssl.tracking_layer.tracking_data import MatchData


@dataclass
class RobotRubric:
    # General
    id: int
    halt: bool

    # Decision
    target_pose: Optional[Tuple[float, float, float]] = None  # x, y, theta
    kick_speed: Tuple[float, float] = (0, 0)  # vx, vz
    spinner: bool = False

    # Path Parameters
    avoid_area: bool = False
    avoid_opponents: list[int] = field(default_factory=list)
    avoid_allies: list[int] = field(default_factory=list)

    @classmethod
    def still(cls, id):
        return cls(id=id, halt=True)


@dataclass
class DecisionData:
    commands: list[RobotRubric]
    world_model: MatchData
