from domain.repositories.task_repository import AbstractTaskRepository
from domain.repositories.user_repository import AbstractUserRepository

from infra.security.permissions.abstract import AbstractPermission

from .user import UserAuthService, UserPermissionService, UserAuthDataService
from .task import TaskService


class UserServiceFactory:
    @classmethod
    def get_auth_data_service(cls, user_repository: AbstractUserRepository):
        return UserAuthDataService(user_repository)

    @classmethod
    def get_auth_service(cls, user_repository: AbstractUserRepository):
        return UserAuthService(user_repository)

    @classmethod
    def get_permission_service(cls, permission_objs: list[AbstractPermission]):
        return UserPermissionService(permission_objs)


class TaskServiceFactory:
    @classmethod
    def get_service(cls, task_repository: AbstractTaskRepository, user_repository: AbstractUserRepository):
        return TaskService(task_repository, user_repository)
