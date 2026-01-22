from pydantic import EmailStr
from dataclasses import dataclass, field
from .tasks import Task


@dataclass
class User:
    tg_name: str
    email: EmailStr
    password: str
    is_active: bool = field(default=False, init=False)
    tasks: list[Task]
