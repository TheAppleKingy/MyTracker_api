from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Task
from src.domain.services import MAX_DEPTH
from src.application.interfaces.repositories import TaskRepositoryInterface


class AlchemyTaskRepository(TaskRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, task_id: int) -> Optional[Task]:
        return await self._session.scalar(select(Task).where(Task.id == task_id))

    async def get_with_parents(self, task_id: int) -> Optional[Task]:
        return await self._session.scalar(
            select(Task).where(Task.id == task_id).options(
                selectinload(Task.parent, recursion_depth=MAX_DEPTH-1)
            )
        )

    async def get_active_tasks(self, user_id: int) -> list[Task]:
        res = await self._session.scalars(
            select(Task).where(
                Task.user_id == user_id, Task.parent_id == None, Task._pass_date == None
            ).options(selectinload(Task.subtasks))
        )
        return res.all()  # type: ignore

    async def get_finished_tasks(self, user_id: int) -> list[Task]:
        res = await self._session.scalars(
            select(Task).where(
                Task.user_id == user_id, Task.parent_id == None, Task._pass_date != None
            ).options(selectinload(Task.subtasks))
        )
        return res.all()  # type: ignore

    async def get_task_with_subtasks(self, from_task_id: int) -> Optional[Task]:
        return await self._session.scalar(
            select(Task).where(Task.id == from_task_id).options(
                selectinload(Task.subtasks)
            )
        )

    async def get_task_tree(self, from_task_id: int) -> Optional[Task]:
        return await self._session.scalar(
            select(Task).where(Task.id == from_task_id).options(
                selectinload(Task.subtasks, recursion_depth=MAX_DEPTH-1)
            )
        )

    async def delete_task(self, task_id: int) -> None:
        return await self._session.execute(delete(Task).where(Task.id == task_id))
