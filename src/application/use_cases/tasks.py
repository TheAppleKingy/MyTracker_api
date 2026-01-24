from src.domain.entities import Task
from src.domain.services import TaskProducerService, TaskPlannerManagerService
from src.application.interfaces.uow import UoWInterface
from src.application.interfaces.repositories import TaskRepositoryInterface
from src.application.dto.task import (
    TaskCreateDTO,
    TaskUpdateDTO
)


__all__ = [
    "ShowTaskTree",
    "ShowTask",
    "CreateTask",
    "UpdateTask",
    "DeleteTask",
    "FinishTask",
    "ForceFinishTask"
]


class BaseTaskUseCase:
    def __init__(
        self,
        uow: UoWInterface,
        task_repo: TaskRepositoryInterface
    ):
        self._uow = uow
        self._task_repo = task_repo


class ShowTaskTree(BaseTaskUseCase):
    async def execute(self, task_id: int):
        async with self._uow:
            return await self._task_repo.get_task_tree(task_id)


class ShowTask(BaseTaskUseCase):
    async def execute(self, task_id: int):
        async with self._uow:
            return await self._task_repo.get_by_id(task_id)


class CreateTask(BaseTaskUseCase):
    async def execute(self, user_id: int, dto: TaskCreateDTO):
        async with self._uow as uow:
            parent = None
            if dto.parent_id:
                parent = await self._task_repo.get_by_id(dto.parent_id)
            manager = TaskProducerService()
            created = manager.create_task(
                dto.title,
                dto.deadline,
                user_id,
                parent,
                dto.description
            )
            uow.save(created)


class UpdateTask(BaseTaskUseCase):
    async def execute(self, task_id: int, dto: TaskUpdateDTO):
        async with self._uow:
            task = await self._task_repo.get_by_id(task_id)
            if dto.title:
                task.title = dto.title
            if dto.description:
                task.description = dto.description
            if dto.deadline:
                manager = TaskPlannerManagerService(task)
                manager.set_deadline(dto.deadline)


class DeleteTask(BaseTaskUseCase):
    async def execute(self, task_id: int):
        async with self._uow:
            return await self._task_repo.delete_task(task_id)


class FinishTask(BaseTaskUseCase):
    async def execute(self, task_id: int):
        async with self._uow:
            task = await self._task_repo.get_nested_task(task_id)
            task.mark_as_done()


class ForceFinishTask(BaseTaskUseCase):
    async def execute(self, task_id: int):
        async with self._uow:
            task = await self._task_repo.get_nested_task(task_id)
            task.force_mark_as_done()
