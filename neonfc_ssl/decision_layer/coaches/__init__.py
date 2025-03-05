from .circle_coach import CircleCoach
from .test_coach import TestCoach
# from .simple_coach import SimpleCoach

from typing import TYPE_CHECKING, Type
if TYPE_CHECKING:
    from .base_coach import Coach

_coach_list: list[Type['Coach']] = [
    # Tournament coaches
    TestCoach,
    # SimpleCoach,
    CircleCoach
]

COACHES: dict[str, Type['Coach']] = {c.__name__: c for c in _coach_list}
