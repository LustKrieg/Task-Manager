from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Task:
    id: Optional[int]
    title: str
    completed: bool
    created_at: datetime
    deleted: bool
    notes: str = ""
