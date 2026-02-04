from typing import Literal, Optional

from fastapi import APIRouter, Query
from dishka.integrations.fastapi import DishkaRoute, FromDishka

from src.application.use_cases import *
from src.application.dto.task import (
    TaskCreateDTO,
    TaskUpdateDTO,
    DeleteResponseDTO,
    TaskViewDTO,
    PaginatedTasksDTO,
    ForceFinishResponseDTO
)
from src.domain.types import AuthenticatedUserId, AuthenticatedOwnerId
from src.logger import logger


task_router = APIRouter(
    prefix='/tasks',
    tags=['API to manage tasks'],
    route_class=DishkaRoute
)


@task_router.get('')
async def get_tasks(
    user_id: FromDishka[AuthenticatedUserId],
    use_case: FromDishka[ShowTasks],
    page: int = Query(ge=1, default=1),
    size: int = Query(default=5),
    status: Literal["active", "finished"] = Query(default="active")
) -> PaginatedTasksDTO:
    prev_page, next_page, tasks = await use_case.execute(user_id, status, page=page, size=size)
    return PaginatedTasksDTO(
        tasks=[TaskViewDTO.model_validate(task) for task in tasks],
        prev_page=prev_page,
        next_page=next_page
    )


@task_router.get('/{task_id}')
async def get_user_task(
    task_id: int,
    user_id: FromDishka[AuthenticatedOwnerId],
    use_case: FromDishka[ShowTask]
) -> TaskViewDTO:
    return await use_case.execute(task_id)


@task_router.post('')
async def create_task(
    user_id: FromDishka[AuthenticatedUserId],
    use_case: FromDishka[CreateTask],
    dto: TaskCreateDTO
) -> TaskViewDTO:
    return await use_case.execute(user_id, dto)


@task_router.get("/{task_id}/subtasks")
async def get_subtasks(
    task_id: int,
    user_id: FromDishka[AuthenticatedOwnerId],
    use_case: FromDishka[ShowSubtasks],
    page: int = Query(ge=1, default=1),
    size: int = Query(default=5),
    status: Literal["active", "finished"] = Query(default="active")
) -> PaginatedTasksDTO:
    prev_page, next_page, tasks = await use_case.execute(status, task_id, page=page, size=size)
    return PaginatedTasksDTO(
        tasks=[TaskViewDTO.model_validate(task) for task in tasks],
        prev_page=prev_page,
        next_page=next_page
    )


@task_router.patch('/{task_id}')
async def update_task(
    user_id: FromDishka[AuthenticatedOwnerId],
    task_id: int,
    use_case: FromDishka[UpdateTask],
    dto: TaskUpdateDTO
) -> TaskViewDTO:
    return await use_case.execute(task_id, dto)


@task_router.patch('/{task_id}/finish')
async def finish_task(
    user_id: FromDishka[AuthenticatedOwnerId],
    use_case: FromDishka[FinishTask],
    task_id: int
):
    await use_case.execute(task_id)


@task_router.patch("/{task_id}/finish/force")
async def force_finish_task(
    user_id: FromDishka[AuthenticatedOwnerId],
    use_case: FromDishka[ForceFinishTask],
    task_id: int
) -> ForceFinishResponseDTO:
    return ForceFinishResponseDTO(subtasks_ids=await use_case.execute(task_id))


@task_router.delete('/{task_id}')
async def delete_task(
    user_id: FromDishka[AuthenticatedOwnerId],
    use_case: FromDishka[DeleteTask],
    task_id: int
) -> DeleteResponseDTO:
    return DeleteResponseDTO(subtasks_ids=await use_case.execute(task_id))


@task_router.get("/{task_id}/is_active")
async def check_task_active(
    task_id: int,
    user_id: FromDishka[AuthenticatedOwnerId],
    use_case: FromDishka[CheckTaskActive]
) -> bool:
    return await use_case.execute(task_id)


@task_router.get("/{task_id}/parent")
async def get_parent_id(
    task_id: int,
    user_id: FromDishka[AuthenticatedOwnerId],
    use_case: FromDishka[ShowParentId]
) -> Optional[int]:
    return await use_case.execute(task_id)
