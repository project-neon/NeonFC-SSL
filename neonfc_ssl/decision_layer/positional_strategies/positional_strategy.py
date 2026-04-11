from abc import ABC, abstractmethod
from neonfc_ssl.decision_layer.decision_data import RobotRubric
from typing import Union

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


POSITION = tuple[float, float]
POSE = tuple[float, float, float]


class PositionalStrategy(ABC):
    @classmethod
    def decide(cls, data: 'MatchData', ids: list[int]):
        return list(map(lambda p: (p, cls), cls.decide_position(data, ids)))

    @staticmethod
    @abstractmethod
    def decide_position(data: 'MatchData', ids: list[int]) -> list[Union[POSITION, POSE]]:
        pass
