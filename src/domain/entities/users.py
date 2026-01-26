from dataclasses import dataclass, field
from .tasks import Task


@dataclass
class User:
    tg_name: str
    id: int = field(default=None, init=False)
    tasks: list[Task] = field(default_factory=list, init=False)
