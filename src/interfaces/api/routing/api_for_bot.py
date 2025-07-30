from fastapi import APIRouter, Depends, status

from domain.entities.users import User

from application.service.task import TaskService
from application.service.user import UserAuthDataService
from application.dto.task_dto import TaskViewForUser, TaskCreateForUser, TaskUpdateForUser
from application.dto.users_dto import CheckIsActive

from infra.security.permissions.permissions import IsActivePermission

from ..dependencies import get_task_service, check_permissions, get_user_auth_data_service


bot_router = APIRouter(
    prefix='/api/bot',
    tags=['BOT']
)


@bot_router.post('/check_is_active', status_code=status.HTTP_200_OK)
async def check_is_active(data: CheckIsActive, service: UserAuthDataService = Depends(get_user_auth_data_service)):
    await service.check_is_active(data.tg_name)


@bot_router.get('/my_tasks', response_model=list[TaskViewForUser])
async def get_my_tasks(user: User = Depends(check_permissions(IsActivePermission())), task_service: TaskService = Depends(get_task_service)):
    return await task_service.get_user_tasks_trees(user.id)


@bot_router.get('/my_task/{id}', response_model=TaskViewForUser)
async def get_my_task(id: int, user: User = Depends(check_permissions(IsActivePermission())), task_service: TaskService = Depends(get_task_service)):
    return await task_service.get_task_tree(id)


@bot_router.post('/create_task', response_model=TaskViewForUser)
async def create_task(task_data: TaskCreateForUser, user: User = Depends(check_permissions(IsActivePermission())), task_service: TaskService = Depends(get_task_service)):
    return await task_service.add_task_to_user(user.id, task_data)


@bot_router.patch('/update_task/{id}', response_model=TaskViewForUser)
async def update_task(id: int, data: TaskUpdateForUser, user: User = Depends(check_permissions(IsActivePermission())), task_service: TaskService = Depends(get_task_service)):
    return await task_service.update_task_for_user(user.id, id, data)


@bot_router.delete('/finish_task/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def finish_task(id: int,  user: User = Depends(check_permissions(IsActivePermission())), task_service: TaskService = Depends(get_task_service)):
    await task_service.finish_task_for_user(user.id, id)
