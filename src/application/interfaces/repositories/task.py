from typing import Protocol, Optional, Literal

from src.domain.entities.tasks import Task


class TaskRepositoryInterface(Protocol):
    async def get_by_id(self, task_id: int) -> Optional[Task]: ...

    async def get_with_parents(self, task_id: int) -> Task: ...

    async def get_with_parent_and_subs(self, task_id: int) -> Task: ...

    async def get_tasks(
        self,
        user_id: int,
        status: Literal["active", "finished"],
        page: int = 1,
        size: int = 5
    ) -> tuple[int, int, list[Task]]: ...

    async def get_subtasks(
        self,
        parent_id: int,
        status: Literal["active", "finished"],
        page: int = 1,
        size: int = 5
    ) -> tuple[int, int, list[Task]]: ...

    async def get_all_subtask_ids(self, task_id: int) -> list[int]: ...

    async def get_task_tree(self, from_task_id: int) -> Task: ...

    async def delete_task(self, task_id: int) -> None: ...
