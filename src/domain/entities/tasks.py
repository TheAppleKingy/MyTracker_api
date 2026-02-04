from datetime import datetime, timezone
from typing import Optional
from collections import deque
from dataclasses import dataclass, field

from .exceptions import (
    UnfinishedTaskError,
    HasNoDirectAccessError,
)


@dataclass
class Task:
    title: str
    _deadline: datetime
    user_id: int
    description: str
    id: int = field(default=None, init=False)  # type: ignore
    creation_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc), init=False)
    _pass_date: Optional[datetime] = field(default=None, init=False)
    parent: Optional["Task"] = None
    parent_id: Optional[int] = field(default=None, init=False)
    subtasks: list['Task'] = field(default_factory=list, init=False)

    @property
    def deadline(self):
        return self._deadline

    @deadline.setter
    def deadline(self, *_):
        raise HasNoDirectAccessError("Cannot set deadline directly")

    @property
    def is_root(self):
        return not bool(self.parent_id)

    @property
    def is_done(self):
        return bool(self._pass_date)

    @property
    def pass_date(self):
        return self._pass_date

    @pass_date.setter
    def pass_date(self, *_):
        raise HasNoDirectAccessError("Cannot set pass date directly")

    def force_mark_as_done(self):
        self._pass_date = datetime.now(timezone.utc)
        for sub in self.subtasks:
            sub.force_mark_as_done()

    def mark_as_done(self):
        queue = deque(self.subtasks)
        while queue:
            current = queue.popleft()
            if not current.is_done:
                raise UnfinishedTaskError("Unable finish task while subtasks not fininshed")
            queue.extend(current.subtasks)
        self._pass_date = datetime.now(timezone.utc)

    def get_depth(self) -> int:
        if self.parent is None:
            return 1
        return self.parent.get_depth() + 1

    def get_subs_ids(self) -> list[int]:
        subs_ids = []

        def collect_ids(task: Task):
            for sub in task.subtasks:
                subs_ids.append(sub.id)
                collect_ids(sub)
        collect_ids(self)
        return subs_ids
