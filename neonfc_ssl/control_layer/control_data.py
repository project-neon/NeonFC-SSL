from dataclasses import dataclass


@dataclass
class RobotCommand:
    id: int
    is_yellow: bool

    vel_tangent: float
    vel_normal: float
    vel_angular: float

    kick_x: float = 0
    kick_z: float = 0

    spinner: bool = False


@dataclass
class ControlData:
    commands: list[RobotCommand]
