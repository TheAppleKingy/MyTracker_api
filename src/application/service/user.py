from domain.entities.users import User
from domain.repositories.user_repository import AbstractUserRepository
from domain.repositories.exceptions import UserRepositoryError

from infra.security.password_utils import hash_password, check_password
from infra.security.token.factory import TokenHandlerFactory as handler_factory
from infra.security.token.exceptions import TokenError
from infra.security.token.base_handler import TokenHandler
from infra.security.permissions.abstract import AbstractPermission
from infra.security.permissions.exc import PermissionException

from application.dto.users_dto import Login, UserCreate, ChangePassword
from .exceptions import UserAuthServiceError, UserPermissionServiceError, UserAuthDataServiceError

from tasks.email import send_mail


class BaseUserService:
    def __init__(self, user_repository: AbstractUserRepository):
        self.repo = user_repository


class BaseUserAuthService(BaseUserService):
    async def validate_user_by_token(self, token: str, token_handler: TokenHandler):
        try:
            payload = token_handler.validate_token(token, ['user_id'])
        except TokenError as e:
            raise UserAuthServiceError(str(e))
        user = await self.repo.get_user(payload['user_id'])
        if not user:
            raise UserAuthServiceError(
                'Not existing user_id was set in token payload. Security threat!')
        return user


class UserAuthService(BaseUserAuthService):
    async def auth_user(self, token: str):
        jwt_handler = handler_factory.get_jwt_handler()
        return await self.validate_user_by_token(token, jwt_handler)


class UserAuthDataService(BaseUserAuthService):
    async def check_is_active(self, tg_name: str):
        users = await self.repo.get_users_by(User.tg_name == tg_name)
        if not users:
            raise UserAuthDataServiceError(
                f"User with tg name {tg_name} does not exist")
        if not users[0].is_active:
            raise UserAuthDataServiceError('User not active')

    def check_user_password(self, password: str, user: User):
        if not check_password(password, user.password):
            raise UserAuthDataServiceError(
                'Wrong password')

    async def validate_user_by_url_token(self, token: str, token_handler: TokenHandler):
        try:
            return await self.validate_user_by_token(token, token_handler)
        except UserAuthServiceError:
            raise UserAuthDataServiceError('Wrong url or expired')

    async def login_user(self, login_schema: Login):
        email, password = login_schema.email, login_schema.password
        user = await self.repo.get_user_by_email(email)
        if not user:
            raise UserAuthDataServiceError(
                f'Unable to find user with email {email}')
        self.check_user_password(password, user)
        return user

    async def registration_request(self, register_schema: UserCreate):
        raw_password = register_schema.password
        password = hash_password(raw_password)
        register_schema.password = password
        try:
            registered = await self.repo.create_user(**register_schema.model_dump(exclude_none=True))
        except UserRepositoryError as e:
            raise UserAuthDataServiceError(str(e))
        token_handler = handler_factory.get_serializer_token_handler()
        confirm_url = token_handler.make_disp_url_for_user(
            'http://localhost:8000/api/profile/confirm/registration/', registered)
        msg = f'Please follow the link for confirm your registration\n{confirm_url}'
        send_mail.delay('Confirm registration', msg, registered.email)

    async def confirm_registration(self, url_token: str):
        token_handler = handler_factory.get_serializer_token_handler()
        user = await self.validate_user_by_url_token(url_token, token_handler)
        if user.is_active:
            raise UserAuthDataServiceError('Your account is already activated')
        await self.repo.update_user(user.id, is_active=True)

    async def change_password_request(self, user_id: int):
        user = await self.repo.get_user(user_id)
        token_handler = handler_factory.get_serializer_token_handler()
        confirm_url = token_handler.make_disp_url_for_user(
            'http://localhost:8000/api/confirm/change_password/', user)
        msg = f'Please follow the link to confirm change password\n{confirm_url}'
        send_mail.delay('Confirm change password', msg, user.email)

    async def confirm_change_password(self, url_token: str, password_change_schema: ChangePassword):
        token_handler = handler_factory.get_serializer_token_handler()
        user = await self.validate_user_by_url_token(url_token, token_handler)
        self.check_user_password(password_change_schema.current_password, user)
        new_password = hash_password(password_change_schema.new_password)
        await self.repo.update_user(user.id, password=new_password)


class UserPermissionService(BaseUserService):
    def __init__(self, permission_objs: list[AbstractPermission]):
        self.perm_objs = permission_objs

    def check(self, user: User) -> User:
        for perm in self.perm_objs:
            try:
                perm.check_user(user)
            except PermissionException as e:
                raise UserPermissionServiceError(str(e))
        return user
