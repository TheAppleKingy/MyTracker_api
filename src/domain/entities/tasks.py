from datetime import datetime, timezone
from typing import Optional


from dataclasses import dataclass, field


@dataclass
class Task:
    title: str
    description: str
    deadline: datetime
    user_id: int
    creation_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc), init=False)
    pass_date: Optional[datetime] = field(default=None, init=False)
    task_id: Optional[int] = None
    subtasks: list['Task'] = field(default_factory=list, init=False)

    @property
    def is_root(self):
        return not bool(self.task_id)

    @property
    def is_done(self):
        return bool(self.pass_date)

    def mark_as_done(self):
        self.pass_date = datetime.now(timezone.utc)
        for sub in self.subtasks:
            sub.mark_as_done()
