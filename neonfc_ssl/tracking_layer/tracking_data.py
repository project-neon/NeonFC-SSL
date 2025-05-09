from dataclasses import dataclass, field as dc_f
from enum import Enum
from typing import Optional
import numpy as np
import math
from neonfc_ssl.protocols.internal import TrackingProtobuf, CommonsProtobuf
from neonfc_ssl.commons.math import reduce_ang, distance_between_points
from neonfc_ssl.input_layer.input_data import Geometry


@dataclass
class TrackedBall:
    x: float
    y: float
    z: Optional[float] = None
    vx: float = None
    vy: float = None
    vz: Optional[float] = None

    speed: float = dc_f(init=False)

    def __post_init__(self):
        self.speed = math.sqrt(self.vx**2 + self.vy**2)

    def __getitem__(self, item):
        if item == 0:
            return self.x

        if item == 1:
            return self.y

        if item == 2:
            return self.z

        raise IndexError("Robot only has 3 coordinates")

    def __array__(self, dtype=None, copy=None):
        if copy is False:
            raise ValueError("`copy=False` isn't supported")
        return np.array([self.x, self.y], dtype=dtype)

    def pos_after(self, dt):
        # t_max = a/v
        # pos = initial_pos + initial_v * t_target + 0.5 * a * t_target ^ 2
        a = 0.8

        t_max_x = abs(self.vx/a) if a else 0
        t_max_y = abs(self.vy/a) if a else 0

        dt_x = min(dt, t_max_x)
        dt_y = min(dt, t_max_y)

        return (self.x + self.vx * dt_x - math.copysign(0.5 * a * dt_x ** 2, self.vx),
                self.y + self.vy * dt_y - math.copysign(0.5 * a * dt_y ** 2, self.vy))

    def stopping_pos(self):
        # t_max = a/v
        # pos = initial_pos + initial_v * t_target + 0.5 * a * t_target ^ 2
        a = 0.005 * math.pi * 9.81
        a = 0.3

        t_max_x = abs(self.vx/a) if a else 0
        t_max_y = abs(self.vy/a) if a else 0

        dt_x = t_max_x
        dt_y = t_max_y

        return (self.x + self.vx * dt_x - math.copysign(0.5 * a * dt_x ** 2, self.vx),
                self.y + self.vy * dt_y - math.copysign(0.5 * a * dt_y ** 2, self.vy))

    def to_proto(self):
        return TrackingProtobuf.Ball(
            pos=CommonsProtobuf.Vector(x=self.x, y=self.y, z=self.z),
            vel=CommonsProtobuf.Vector(x=self.vx, y=self.vy, z=self.vz),
        )


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

    def __array__(self, dtype=None, copy=None):
        if copy is False:
            raise ValueError("`copy=False` isn't supported")
        return np.array([self.x, self.y], dtype=dtype)

    def time_to_ball(self, ball):
        avg_speed = .35
        pos = np.array(ball)
        last_t = 0
        for _ in range(50):
            t = distance_between_points(pos, self) / avg_speed
            pos = ball.pos_after(t)

            if abs(t - last_t) < 0.01:
                return t

            last_t = t
        return last_t

    def to_proto(self):
        return TrackingProtobuf.Robot(
            id=self.id,
            color=CommonsProtobuf.Colors.Value(color),
            pos=CommonsProtobuf.Vector(x=self.x, y=self.y, z=self.theta),
            vel=CommonsProtobuf.Vector(x=self.vx, y=self.vy, z=self.vtheta),
        )


@dataclass
class RobotList:
    robots: list[TrackedRobot]
    active: list[TrackedRobot] = dc_f(init=False)

    def __post_init__(self):
        self.active = [r for r in self.robots if not r.missing]

    def __getitem__(self, item):
        return self.robots[item]

    @property
    def actives(self):
        return self.active

    def to_proto(self):
        return [r.to_proto() for r in self.robots]


@dataclass
class Possession:
    my_closest: int
    op_closest: int

    possession_balance: float

    contact_start_position: np.array

    def to_proto(self):
        return TrackingProtobuf.Possession(
            balance=self.possession_balance
        )


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
    friendly: Optional[bool] = None
    position: Optional[tuple[float, float]] = None

    def to_proto(self):
        return TrackingProtobuf.GameState(
            state=TrackingProtobuf.States.Value(self.state),
            team=CommonsProtobuf.Colors.Value(color),
            pos=CommonsProtobuf.Vector(x=self.x, y=self.y, z=self.theta),
            vel=CommonsProtobuf.Vector(x=self.vx, y=self.vy, z=self.vtheta),
        )


@dataclass
class MatchData:
    ball: TrackedBall
    possession: Possession
    game_state: GameState
    field: Geometry
    robots: RobotList = dc_f()
    opposites: RobotList
    is_yellow: bool

    def __post_init__(self):
        self.robots = RobotList(self.robots)
        self.opposites = RobotList(self.opposites)

    def to_proto(self):
        return TrackingProtobuf.Tracking(
            team_color=CommonsProtobuf.Colors.Value('yellow' if self.is_yellow else 'blue'),
            ball=self.ball.to_proto(),
            robots=self.robots.to_proto(),
            opposites=self.opposites.to_proto(),
            game_state=self.game_state.to_proto(),
            possession=self.possession.to_proto()
        )
