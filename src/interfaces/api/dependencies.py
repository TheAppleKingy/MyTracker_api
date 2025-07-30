from fastapi import Depends, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from infra.db.session import get_db_session
from infra.db.repository.user_repo import UserRepository
from infra.db.repository.task_repo import TaskRepository
from infra.db.repository.factories import UserRepoFactory, TaskRepoFactory
from domain.entities.users import User
from infra.security.permissions.abstract import AbstractPermission
from application.service.factories import UserServiceFactory, TaskServiceFactory
from application.service.user import UserAuthService


def get_user_repo(session: AsyncSession = Depends(get_db_session)):
    return UserRepoFactory.get_user_repository(session)


def get_task_repo(session: AsyncSession = Depends(get_db_session)):
    return TaskRepoFactory.get_task_repository(session)


def get_user_auth_data_service(user_repo: UserRepository = Depends(get_user_repo)):
    return UserServiceFactory.get_auth_data_service(user_repo)


def get_user_auth_service(user_repo: UserRepository = Depends(get_user_repo)):
    return UserServiceFactory.get_auth_service(user_repo)


def get_task_service(task_repo: TaskRepository = Depends(get_task_repo), user_repo: UserRepository = Depends(get_user_repo)):
    return TaskServiceFactory.get_service(task_repo, user_repo)


async def authenticate(token: str = Cookie(default=None, include_in_schema=False), auth_service: UserAuthService = Depends(get_user_auth_service)):
    return await auth_service.auth_user(token)


def check_permissions(*required_permissions: AbstractPermission):
    def checker(user: User = Depends(authenticate)):
        permission_service = UserServiceFactory.get_permission_service(
            required_permissions)
        return permission_service.check(user)
    return checker
