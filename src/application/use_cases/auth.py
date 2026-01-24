from src.domain.entities import User
from src.application.interfaces.uow import UoWInterface
from src.application.interfaces.repositories import UserRepositoryInterface
from src.application.interfaces.services import PasswordServiceInterface, AuthenticationServiceInterface
from src.application.dto.users import LoginUserDTO, RegisterUserDTO, ChangePasswordDTO
from .exceptions import (
    UndefinedUserError,
    InvalidUserPasswordError,
    UserExistsError
)


class LoginUser:
    def __init__(
        self,
        uow: UoWInterface,
        user_repo: UserRepositoryInterface,
        password_service: PasswordServiceInterface,
        auth_service: AuthenticationServiceInterface
    ):
        self._uow = uow
        self._user_repo = user_repo
        self._password_service = password_service
        self._auth_service = auth_service

    async def execute(self, dto: LoginUserDTO) -> str:
        async with self._uow:
            user = await self._user_repo.get_by_tg_name(dto.tg_name)
        if not user:
            raise UndefinedUserError("User not found")
        if not self._password_service.check_password(user.password, dto.password):
            raise InvalidUserPasswordError("Incorrect password")
        return self._auth_service.generate_token(user.id)


class RegisterUser:
    def __init__(
        self,
        uow: UoWInterface,
        user_repo: UserRepositoryInterface,
        password_service: PasswordServiceInterface,
        auth_service: AuthenticationServiceInterface
    ):
        self._uow = uow
        self._user_repo = user_repo
        self._password_service = password_service
        self._auth_service = auth_service

    async def execute(self, dto: RegisterUserDTO) -> str:
        async with self._uow as uow:
            count = await self._user_repo.count_by_tg_name(dto.tg_name)
            if count:
                raise UserExistsError("User with this telegram name already exists")
            registered = User(dto.tg_name, self._password_service.hash_password(dto.password))
            uow.save(registered)
            await uow.flush()
            return self._auth_service.generate_token(registered.id)


class ChangePassword:
    def __init__(
        self,
        uow: UoWInterface,
        user_repo: UserRepositoryInterface,
        password_service: PasswordServiceInterface,
    ):
        self._uow = uow
        self._user_repo = user_repo
        self._password_service = password_service

    async def execute(self, tg_name: str, dto: ChangePasswordDTO):
        async with self._uow:
            user = await self._user_repo.get_by_tg_name(tg_name)
            user.password = self._password_service.hash_password(dto.new_password)
