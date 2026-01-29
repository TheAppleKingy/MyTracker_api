from src.logger import logger
from datetime import datetime, timezone
from typing import Optional
from collections import deque

from src.domain.entities import Task
from src.domain.services.exceptions import (
    MaxDepthError,
    InvalidDeadlineError,
    ParentFinishedError
)

MAX_DEPTH = 5


class BaseTaskManagerService:
    def _validate_deadline(self, to_set: datetime):
        if datetime.now(timezone.utc) >= to_set.astimezone(timezone.utc):
            raise InvalidDeadlineError("Deadline cannot be less or equal than now")


class TaskProducerService(BaseTaskManagerService):
    def _validate_depth(self, parent: Task):
        if parent.get_depth() >= MAX_DEPTH:
            raise MaxDepthError(f"Depth of task tree couldn't be more than {MAX_DEPTH}")

    def create_task(
        self,
        title: str,
        deadline: datetime,
        user_id: int,
        description: str,
        parent: Optional[Task] = None,
    ):
        self._validate_deadline(deadline)
        if parent:
            self._validate_depth(parent)
            if parent.is_done:
                raise ParentFinishedError("Unable to create subtasks of fnished parent task")
            if parent.deadline < deadline:
                raise InvalidDeadlineError(
                    "Deadline of creating task cannot be more than deadline of parent task")
        return Task(
            title,
            deadline,
            user_id,
            description=description,
            parent=parent
        )


class TaskPlannerManagerService(BaseTaskManagerService):
    def __init__(self, task: Task):
        self._task = task

    def _validate_subs_deadlines(self, new_deadline: datetime):
        queue: deque[Task] = deque(self._task.subtasks)
        while queue:
            current = queue.popleft()
            if current.deadline > new_deadline:
                raise InvalidDeadlineError(
                    "Deadline of creating task cannot be less than deadline of subtasks")
            queue.extend(current.subtasks)

    def _validate_parent_deadline(self, new_deadline: datetime):
        if self._task.parent.deadline < new_deadline:  # type: ignore
            raise InvalidDeadlineError(
                "Deadline of creating task cannot be more than deadline of parent task")

    def _validate_deadline(self, to_set: datetime):
        super()._validate_deadline(to_set)
        self._validate_parent_deadline(to_set)
        self._validate_subs_deadlines(to_set)

    def set_deadline(self, new_dealine: datetime):
        self._validate_deadline(new_dealine)
        self._task._deadline = new_dealine
