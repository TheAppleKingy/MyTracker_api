from typing import Protocol

from src.domain.entities.tasks import Task


class TaskRepositoryInterface(Protocol):
    async def get_by_id(self, task_id: int) -> Task | None: ...

    async def get_root_tasks(self) -> list[Task]: ...

    async def get_root_tasks_for_user(self, user_id: int) -> list[Task]: ...

    async def get_nested_tasks(
        self, from_task_id: int, return_list: bool = False) -> Task | list[Task]: ...
