from typing import Optional

from src.domain.entities import User
from src.application.interfaces.uow import UoWInterface
from src.domain.types import AuthenticatedUserId, AuthenticatedOwnerId
from src.application.interfaces.repositories import UserRepositoryInterface, TaskRepositoryInterface
from src.application.interfaces.services import AuthenticationServiceInterface
from src.application.dto.users import RegisterUserDTO
from .exceptions import (
    UndefinedUserError,
    UserExistsError,
    UndefinedTaskError,
    HasNoAccessError
)
from src.logger import logger
__all__ = [
    "RegisterUser",
    "AuthenticateUser",
    "AuthenticateTaskOwner",
    "CheckUserExists"
]


class RegisterUser:
    def __init__(
        self,
        uow: UoWInterface,
        user_repo: UserRepositoryInterface,
    ):
        self._uow = uow
        self._user_repo = user_repo

    async def execute(self, dto: RegisterUserDTO):
        async with self._uow as uow:
            count = await self._user_repo.count_by_tg_name(dto.tg_name)
            if count:
                raise UserExistsError("User with this telegram name already exists")
            registered = User(dto.tg_name)
            uow.save(registered)


class CheckUserExists:
    def __init__(
        self,
        uow: UoWInterface,
        user_repo: UserRepositoryInterface,
    ):
        self._uow = uow
        self._user_repo = user_repo

    async def execute(self, tg_name: str) -> bool:  # type: ignore
        async with self._uow:
            return bool(await self._user_repo.count_by_tg_name(tg_name))


class AuthenticateUser:
    def __init__(
        self,
        uow: UoWInterface,
        user_repo: UserRepositoryInterface,
        auth_service: AuthenticationServiceInterface
    ):
        self._uow = uow
        self._user_repo = user_repo
        self._auth_service = auth_service

    async def execute(self, token: Optional[str]):
        if not token:
            raise UndefinedUserError("Unauthorized", status=401)
        tg_name = self._auth_service.get_tg_name_from_token(token)
        async with self._uow:
            user = await self._user_repo.get_by_tg_name(tg_name)
            if not user:
                raise UndefinedUserError("Unauthorized", status=401)
        return AuthenticatedUserId(user.id)  # type: ignore


class AuthenticateTaskOwner:
    def __init__(
        self,
        uow: UoWInterface,
        task_repo: TaskRepositoryInterface
    ):
        self._uow = uow
        self._task_repo = task_repo

    async def execute(self, task_id: int, user_id: AuthenticatedUserId):
        async with self._uow:
            task = await self._task_repo.get_by_id(task_id)
            if not task:
                raise UndefinedTaskError("Unable to find task", status=404)
            if task.user_id != user_id:
                raise HasNoAccessError("User has no access the task", status=403)
        return AuthenticatedOwnerId(user_id)
