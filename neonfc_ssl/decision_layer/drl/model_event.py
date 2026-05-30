from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelReference:
    id: str
    file_path: str
    transformation: Optional[str]
