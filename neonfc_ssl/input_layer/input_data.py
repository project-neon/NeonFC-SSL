from dataclasses import dataclass
from typing import Optional


@dataclass
class Ball:
    x: float
    y: float
    z: Optional[float] = None
    vx: Optional[float] = None
    vy: Optional[float] = None
    vz: Optional[float] = None

    timestamp: Optional[float] = None
    confidence: Optional[float] = None
    camera_id: Optional[int] = None


@dataclass
class Robot:
    id: int
    team: str

    x: float
    y: float
    theta: float
    vx: Optional[float] = None
    vy: Optional[float] = None
    vtheta: Optional[float] = None

    timestamp: Optional[float] = None
    confidence: Optional[float] = None
    camera_id: Optional[int] = None


@dataclass
class Entities:
    ball: Ball
    robots_blue: dict[int, Robot]
    robots_yellow: dict[int, Robot]


@dataclass
class Geometry:
    field_length: float
    field_width: float
    goal_width: float
    penalty_depth: float
    penalty_width: float


@dataclass
class GameController:
    can_play: bool
    state: str
    designated_position: tuple[int, int]
    team: str


@dataclass
class InputData:
    entities: Entities
    geometry: Geometry
    game_controller: GameController

