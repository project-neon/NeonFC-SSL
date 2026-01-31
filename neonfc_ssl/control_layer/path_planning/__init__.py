from .rrt.rrt_planner import RRTPlanner, RRTStarPlanner
from .velocity_obstacle.vo_planner import VOPlanner

from typing import TYPE_CHECKING, Type
if TYPE_CHECKING:
    from .base_planner import Planner
    
_planner_list: list[Type['Planner']] = [
    # Available planners
    RRTPlanner,
    RRTStarPlanner,
    VOPlanner
]

PLANNERS: dict[str, Type['Planner']] = {p.__name__: p for p in _planner_list}
