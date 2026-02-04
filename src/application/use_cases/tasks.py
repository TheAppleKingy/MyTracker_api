from typing import Literal

from src.domain.entities import Task
from src.domain.services import TaskProducerService, TaskPlannerManagerService
from src.application.interfaces.uow import UoWInterface
from src.application.interfaces.repositories import TaskRepositoryInterface
from src.application.dto.task import (
    TaskCreateDTO,
    TaskUpdateDTO
)
from src.domain.types import AuthenticatedUserId
from .exceptions import UndefinedTaskError, TaskAlreadyFinishedError

__all__ = [
    "ShowTask",
    "ShowSubtasks",
    "ShowTasks",
    "CreateTask",
    "UpdateTask",
    "DeleteTask",
    "FinishTask",
    "ForceFinishTask",
    "CheckTaskActive",
    "ShowParentId"
]


class BaseTaskUseCase:
    def __init__(
        self,
        uow: UoWInterface,
        task_repo: TaskRepositoryInterface
    ):
        self._uow = uow
        self._task_repo = task_repo


class ShowTask(BaseTaskUseCase):
    async def execute(self, task_id: int):
        async with self._uow:
            return await self._task_repo.get_by_id(task_id)


class ShowSubtasks(BaseTaskUseCase):
    async def execute(
        self,
        status: Literal["active", "finished"],
        parent_id: int,
        page: int = 1,
        size: int = 5,
    ) -> tuple[int, int, list[Task]]:  # type: ignore
        async with self._uow:
            return await self._task_repo.get_subtasks(parent_id, status, page=page, size=size)


class ShowTasks(BaseTaskUseCase):
    async def execute(
        self,
        user_id: AuthenticatedUserId,
        status: Literal["active", "finished"],
        page: int = 1,
        size: int = 5
    ) -> tuple[int, int, list[Task]]:  # type: ignore
        async with self._uow:
            return await self._task_repo.get_tasks(user_id, status, page=page, size=size)


class CreateTask(BaseTaskUseCase):
    async def execute(self, user_id: AuthenticatedUserId, dto: TaskCreateDTO):
        async with self._uow as uow:
            parent = None
            if dto.parent_id:
                parent = await self._task_repo.get_with_parents(dto.parent_id)
                if not parent:
                    raise UndefinedTaskError("Unable to bind to unexistent parent task")
            manager = TaskProducerService()
            created = manager.create_task(
                dto.title,
                dto.deadline,
                user_id,
                dto.description,
                parent,
            )
            uow.save(created)
        return created


class UpdateTask(BaseTaskUseCase):
    async def execute(self, task_id: int, dto: TaskUpdateDTO):
        async with self._uow:
            task = await self._task_repo.get_with_parent_and_subs(task_id)
            if dto.title:
                task.title = dto.title
            if dto.description:
                task.description = dto.description
            if dto.deadline:
                manager = TaskPlannerManagerService(task)
                manager.set_deadline(dto.deadline)
        return task


class DeleteTask(BaseTaskUseCase):
    async def execute(self, task_id: int):
        async with self._uow:
            subs_ids = await self._task_repo.get_all_subtask_ids(task_id)
            await self._task_repo.delete_task(task_id)
            return subs_ids


class FinishTask(BaseTaskUseCase):
    async def execute(self, task_id: int):
        async with self._uow:
            task = await self._task_repo.get_task_tree(task_id)
            if task.is_done:
                raise TaskAlreadyFinishedError("Task already finished")
            task.mark_as_done()


class CheckTaskActive(BaseTaskUseCase):
    async def execute(self, task_id: int):
        async with self._uow:
            task = await self._task_repo.get_by_id(task_id)
            return not task.is_done


class ShowParentId(BaseTaskUseCase):
    async def execute(self, task_id: int):
        async with self._uow:
            task = await self._task_repo.get_by_id(task_id)
            return task.parent_id


class ForceFinishTask(BaseTaskUseCase):
    async def execute(self, task_id: int):
        async with self._uow:
            task = await self._task_repo.get_task_tree(task_id)
            if task.is_done:
                raise TaskAlreadyFinishedError("Task already finished")
            task.force_mark_as_done()
            return task.get_subs_ids()
