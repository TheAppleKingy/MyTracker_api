from typing import Optional, TypedDict

from sqlalchemy import select, delete, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Task
from src.domain.services import MAX_DEPTH
from src.application.interfaces.repositories import TaskRepositoryInterface


class AlchemyTaskRepository(TaskRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, task_id: int) -> Optional[Task]:
        return await self._session.scalar(select(Task).where(Task.id == task_id))  # type: ignore

    async def get_with_parents(self, task_id: int) -> Task:
        return await self._session.scalar(
            select(Task).where(Task.id == task_id).options(  # type: ignore
                selectinload(Task.parent, recursion_depth=MAX_DEPTH-1)  # type: ignore
            )
        )

    async def get_with_parent_and_subs(self, task_id: int) -> Task:
        return await self._session.scalar(
            select(Task).where(Task.id == task_id).options(  # type: ignore
                selectinload(Task.parent),  # type: ignore
                selectinload(Task.subtasks, recursion_depth=MAX_DEPTH-1)  # type: ignore
            )
        )

    def _pagination_query(self, page: int = 1, size: int = 5):
        return (
            select(Task)
            .offset((page - 1) * size)
            .limit(size + 1)
            .order_by(desc(Task.creation_date))  # type: ignore
        )

    def _build_paginated_result(self, tasks: list[Task], page: int, size: int):
        has_next = len(tasks) > size
        return page - 1 if page > 1 and tasks else 0, page + 1 if has_next else 0, tasks[:-1] if has_next else tasks

    async def get_active_tasks(self, user_id: int, page: int = 1, size: int = 5) -> tuple[int, int, list[Task]]:
        res = await self._session.scalars(self._pagination_query(page, size).where(
            Task.user_id == user_id, Task.parent_id == None, Task._pass_date == None  # type: ignore
        ))
        return self._build_paginated_result(res.all(), page, size)  # type: ignore

    async def get_finished_tasks(self, user_id: int, page: int = 1, size: int = 5) -> tuple[int, int, list[Task]]:
        res = await self._session.scalars(self._pagination_query(page, size).where(
            Task.user_id == user_id, Task.parent_id == None, Task._pass_date != None  # type: ignore
        ))
        return self._build_paginated_result(res.all(), page, size)  # type: ignore

    async def get_subtasks(self, parent_id: int, page: int = 1, size: int = 5) -> tuple[int, int, list[Task]]:
        res = await self._session.scalars(self._pagination_query(page, size).where(
            Task.parent_id == parent_id  # type: ignore
        ))
        return self._build_paginated_result(res.all(), page, size)  # type: ignore

    async def get_task_with_subtasks(self, from_task_id: int) -> Task:
        return await self._session.scalar(
            select(Task).where(Task.id == from_task_id).options(  # type: ignore
                selectinload(Task.subtasks)  # type: ignore
            )
        )

    async def get_task_tree(self, from_task_id: int) -> Task:
        return await self._session.scalar(
            select(Task).where(Task.id == from_task_id).options(  # type: ignore
                selectinload(Task.subtasks, recursion_depth=MAX_DEPTH-1)  # type: ignore
            )
        )

    async def delete_task(self, task_id: int) -> None:
        return await self._session.execute(delete(Task).where(Task.id == task_id))  # type: ignore
