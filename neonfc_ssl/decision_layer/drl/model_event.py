from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelReference:
    id: str
    file_path: str
    epsilon: float = 0
    transformation: Optional[str] = None
