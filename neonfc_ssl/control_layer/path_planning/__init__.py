from .base_planner import Planner
from .rrt.rrt_planner import RRTPlanner, RRTStarPlanner

from typing import TYPE_CHECKING, Type
if TYPE_CHECKING:
    from .base_planner import Planner

_planner_list: list[Type['Planner']] = {
    RRTPlanner,
    RRTStarPlanner
}

PLANNERS: dict[str, Type['Planner']] = {p.__name__: p for p in _planner_list}
