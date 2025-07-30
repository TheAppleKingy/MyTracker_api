from sqlalchemy.ext.asyncio import AsyncSession

from domain.repositories.task_repository import AbstractTaskRepository
from domain.repositories.user_repository import AbstractUserRepository
from .user_repo import UserRepository
from .task_repo import TaskRepository


class UserRepoFactory:
    @classmethod
    def get_user_repository(cls, session: AsyncSession) -> AbstractUserRepository:
        return UserRepository(session)


class TaskRepoFactory:
    @classmethod
    def get_task_repository(cls, session: AsyncSession) -> AbstractTaskRepository:
        return TaskRepository(session)
