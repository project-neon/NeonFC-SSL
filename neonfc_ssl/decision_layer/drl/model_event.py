from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelReference:
    id: str
    file_path: str
    robot_id: Optional[int] = None
    epsilon: float = 0
    transformation: Optional[str] = None
