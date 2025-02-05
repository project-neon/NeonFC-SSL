from dataclasses import dataclass
from enum import Enum
from typing import Optional
from neonfc_ssl.input_l.input_data import Geometry


@dataclass
class TrackedBall:
    x: float
    y: float
    z: Optional[float] = None
    vx: float = None
    vy: float = None
    vz: Optional[float] = None

    def __getitem__(self, item):
        if item == 0:
            return self.x

        if item == 1:
            return self.y

        if item == 2:
            return self.z

        raise IndexError("Robot only has 3 coordinates")


@dataclass
class TrackedRobot:
    id: int
    color: str

    x: float
    y: float
    theta: float
    vx: float
    vy: float
    vtheta: float

    missing: float

    def __getitem__(self, item):
        if item == 0:
            return self.x

        if item == 1:
            return self.y

        if item == 2:
            return self.theta

        raise IndexError("Robot only has 3 coordinates")


@dataclass
class Possession:
    my_closest: int
    op_closest: int

    possession_balance: float


class States(Enum):
    HALT = 'Halt'
    STOP = 'TimeOut'
    TIMEOUT = 'Stop'
    PREPARE_KICKOFF = 'PrepareKickOff'
    PREPARE_PENALTY = 'BallPlacement'
    BALL_PLACEMENT = 'PreparePenalty'
    KICKOFF = 'KickOff'
    FREE_KICK = 'FreeKick'
    PENALTY = 'Penalty'
    RUN = 'Run'


@dataclass
class GameState:
    state: States
    color: Optional[str] = None
    position: Optional[tuple[float, float]] = None


@dataclass
class Field:
    fieldLength: int
    fieldWidth: int
    penaltyAreaDepth: int
    penaltyAreaWidth: int
    goalWidth: int


@dataclass
class MatchData:
    robots: list[TrackedRobot]
    opposites: list[TrackedRobot]
    ball: TrackedBall
    possession: Possession
    game_state: GameState
    field: Geometry

