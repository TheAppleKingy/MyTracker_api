from fastapi import APIRouter
from dishka.integrations.fastapi import DishkaRoute, FromDishka

from src.application.use_cases import *
from src.application.dto.task import (
    TaskCreateDTO,
    TaskUpdateDTO,
    TaskViewForUserDTO
)
from src.domain.types import AuthenticatedUserId, AuthenticatedOwnerId


task_router = APIRouter(
    prefix='/tasks',
    tags=['API to manage tasks'],
    route_class=DishkaRoute
)


@task_router.get('/')
async def get_user_tasks(
    user_id: FromDishka[AuthenticatedUserId],
    use_case: FromDishka[ShowUserTaskTrees]
) -> list[TaskViewForUserDTO]:
    return await use_case.execute(user_id)


@task_router.get('/{task_id}')
async def get_user_task_tree(
    task_id: int,
    user_id: FromDishka[AuthenticatedOwnerId],
    use_case: FromDishka[ShowTaskTree]
):
    return await use_case.execute(task_id)


@task_router.post('/')
async def create_task(
    user_id: FromDishka[AuthenticatedUserId],
    use_case: FromDishka[CreateTask],
    dto: TaskCreateDTO
):
    return await use_case.execute(user_id, dto)


@task_router.patch('/{task_id}')
async def update_task(
    user_id: FromDishka[AuthenticatedOwnerId],
    task_id: int,
    use_case: FromDishka[UpdateTask],
    dto: TaskUpdateDTO
):
    return await use_case.execute(task_id, dto)


@task_router.patch('/{task_id}/finish')
async def finish_task(
    user_id: FromDishka[AuthenticatedOwnerId],
    use_case: FromDishka[FinishTask],
    task_id: int
):
    return await use_case.execute(task_id)


@task_router.patch("/{task_id}/finish/force")
async def force_finish_task(
    user_id: FromDishka[AuthenticatedOwnerId],
    use_case: FromDishka[ForceFinishTask],
    task_id: int
):
    return await use_case.execute(task_id)


@task_router.delete('/{task_id}')
async def delete_task(
    user_id: FromDishka[AuthenticatedOwnerId],
    use_case: FromDishka[DeleteTask],
    task_id: int
):
    return await use_case.execute(task_id)
