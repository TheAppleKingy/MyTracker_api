import pytest

import config

from datetime import datetime, timedelta

from freezegun import freeze_time

from domain.entities.tasks import Task
from domain.entities.users import User
from infra.db.repository.user_repo import UserRepository
from domain.repositories.exceptions import UserRepositoryError
from infra.security.token.factory import TokenHandlerFactory as handler_factory
from infra.security.token.serializer_handler import SerializerTokenHandler
from infra.security.permissions.permissions import IsActivePermission
from infra.security.password_utils import hash_password
from application.service.user import UserAuthService, UserPermissionService, UserAuthDataService
from application.service.exceptions import UserAuthServiceError, UserPermissionServiceError, UserAuthDataServiceError
from application.dto.users_dto import Login, UserCreate, ChangePassword


pytest_mark_asyncio = pytest.mark.asyncio


"""Test auth_user"""


@pytest_mark_asyncio
async def test_auth_user_success(auth_service: UserAuthService, mock_user_repo: UserRepository):
    user = User(id=1)
    jwt_handler = handler_factory.get_jwt_handler()
    token = jwt_handler.get_token_for_user(user)
    mock_user_repo.get_user.return_value = user
    result = await auth_service.auth_user(token)
    assert result == user


@pytest_mark_asyncio
async def test_auth_user_invalid_token(auth_service: UserAuthService):
    jwt_handler = handler_factory.get_jwt_handler()
    token = jwt_handler.get_token_for_user(User(id=1))[:-1]
    with pytest.raises(UserAuthServiceError):
        await auth_service.auth_user(token)


@pytest_mark_asyncio
async def test_auth_user_token_expired(auth_service: UserAuthService):
    jwt_handler = handler_factory.get_jwt_handler()
    token = jwt_handler.get_token_for_user(User(id=1))
    with freeze_time(datetime.now()+timedelta(seconds=config.TOKEN_EXPIRE_TIME+3)):
        with pytest.raises(UserAuthServiceError):
            await auth_service.auth_user(token)


@pytest_mark_asyncio
async def test_auth_user_token_is_none(auth_service: UserAuthService):
    with pytest.raises(UserAuthServiceError, match='token was not provide'):
        await auth_service.auth_user(None)


@pytest_mark_asyncio
async def test_auth_user_token_does_not_contain_fields(auth_service: UserAuthService):
    jwt_handler = handler_factory.get_jwt_handler()
    token = jwt_handler.encode({'other': 33})
    with pytest.raises(UserAuthServiceError, match='provided token does not contain required info'):
        await auth_service.auth_user(token)


@pytest_mark_asyncio
async def test_auth_user_fail_invalid_id(auth_service: UserAuthService, mock_user_repo: UserRepository):
    mock_user_repo.get_user.return_value = None
    jwt_handler = handler_factory.get_jwt_handler()
    token = jwt_handler.get_token_for_user(User(id=1))
    with pytest.raises(UserAuthServiceError, match="Security threat"):
        await auth_service.auth_user(token)


"""test login"""


@pytest_mark_asyncio
async def test_login_user_success(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository, mocker):
    user = User(email="test@example.com", password="hashed")
    mock_user_repo.get_user_by_email.return_value = user
    schema = Login(email=user.email, password=user.password)
    mocker.patch("application.service.user.check_password", return_value=True)
    result = await auth_data_service.login_user(schema)
    assert result == user


@pytest_mark_asyncio
async def test_login_user_wrong_password(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository, mocker):
    user = User(email="test@example.com", password="hashed")
    mock_user_repo.get_user_by_email.return_value = user
    mocker.patch("application.service.user.check_password", return_value=False)
    schema = Login(email=user.email, password=user.password)
    with pytest.raises(UserAuthDataServiceError, match="Wrong password"):
        await auth_data_service.login_user(schema)


@pytest_mark_asyncio
async def test_login_user_not_found(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository):
    mock_user_repo.get_user_by_email.return_value = None
    schema = Login(email='te', password='tp')
    with pytest.raises(UserAuthDataServiceError, match="Unable to find user"):
        await auth_data_service.login_user(schema)


"""test registration"""


@pytest_mark_asyncio
async def test_register_request_success(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository, mocker):
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    user = User(id=1, email="test@test.com")
    mock_user_repo.create_user.return_value = user
    schema = UserCreate(
        tg_name='testtg', email='test@test.com', password='test_pass')
    await auth_data_service.registration_request(schema)
    mock_user_repo.create_user.assert_awaited_once()
    mock_send_mail.assert_called_once()
    args, kwargs = mock_send_mail.call_args
    assert user.email in args


@pytest_mark_asyncio
async def test_register_user_fail_duplicate(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository, mocker):
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    mock_user_repo.create_user.side_effect = UserRepositoryError(
        'already exists')
    mocker.patch("domain.repositories.exceptions.parse_integrity_err_message",
                 return_value=("email", "dw"))
    schema = UserCreate(
        tg_name='testtg', email='lala@mail.ru', password='test_pass')
    with pytest.raises(UserAuthDataServiceError, match="already exists"):
        await auth_data_service.registration_request(schema)
        mock_send_mail.assert_not_called()


@pytest_mark_asyncio
async def test_confirm_registration(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository):
    user = User(id=1)
    token_handler = handler_factory.get_serializer_token_handler()
    url_token = token_handler.encode({'user_id': user.id})
    mock_user_repo.get_user.return_value = user
    await auth_data_service.confirm_registration(url_token)


@pytest_mark_asyncio
async def test_confirm_registration_wrong_url_token(auth_data_service: UserAuthDataService):
    user = User(id=1)
    token_handler = handler_factory.get_serializer_token_handler()
    url_token = token_handler.encode({'user_id': user.id})[:-1]
    with pytest.raises(UserAuthDataServiceError):
        await auth_data_service.confirm_registration(url_token)


@pytest_mark_asyncio
async def test_confirm_registration_token_is_none(auth_data_service: UserAuthDataService):
    with pytest.raises(UserAuthDataServiceError):
        await auth_data_service.confirm_registration(None)


@pytest_mark_asyncio
async def test_confirm_registration_token_expired(auth_data_service: UserAuthDataService):
    user = User(id=1)
    token_handler = handler_factory.get_serializer_token_handler()
    url_token = token_handler.encode({'user_id': user.id})
    with freeze_time(datetime.now()+timedelta(seconds=config.URL_EXPIRE_TIME+3)):
        with pytest.raises(UserAuthDataServiceError):
            await auth_data_service.confirm_registration(url_token)


@pytest_mark_asyncio
async def test_confirm_registration_user_is_none(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository, mock_serializer_handler: SerializerTokenHandler, mocker):
    mock_serializer_handler.validate_token.return_value = {'user_id': 1}
    mocker.patch('application.service.user.handler_factory.get_serializer_token_handler',
                 return_value=mock_serializer_handler)
    mock_user_repo.get_user.return_value = None
    with pytest.raises(UserAuthDataServiceError, match='Wrong url or expired'):
        await auth_data_service.confirm_registration('token')


@pytest_mark_asyncio
async def test_confirm_registration_user_already_active(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository, mock_serializer_handler: SerializerTokenHandler):
    user = User(id=1, is_active=True)
    token_handler = handler_factory.get_serializer_token_handler()
    url_token = token_handler.encode({'user_id': user.id})
    mock_user_repo.get_user.return_value = user
    with pytest.raises(UserAuthDataServiceError, match='Your account is already activated'):
        await auth_data_service.confirm_registration(url_token)


"""test change password"""


@pytest_mark_asyncio
async def test_change_password_request(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository, mocker):
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    user = User(id=1, email='email')
    mock_user_repo.get_user.return_value = user
    await auth_data_service.change_password_request(user.id)
    mock_send_mail.assert_called_once()
    args, kwargs = mock_send_mail.call_args
    assert user.email in args


@pytest_mark_asyncio
async def test_change_password_request_user_is_none(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository, mocker):
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    mock_user_repo.get_user.return_value = None
    with pytest.raises(AttributeError):
        await auth_data_service.change_password_request(0)
    mock_send_mail.assert_not_called()


@pytest_mark_asyncio
async def test_confirm_change_password(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository):
    user = User(id=1)
    user.password = hash_password('test')
    token_handler = handler_factory.get_serializer_token_handler()
    url_token = token_handler.encode({'user_id': user.id})
    mock_user_repo.get_user.return_value = user
    schema = ChangePassword(
        current_password='test', new_password='test1')
    await auth_data_service.confirm_change_password(url_token, schema)
    mock_user_repo.update_user.assert_awaited_once()


@pytest_mark_asyncio
async def test_confirm_change_password_wrong_url_token(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository):
    user = User(id=1)
    token_handler = handler_factory.get_serializer_token_handler()
    token = token_handler.encode({'user_id': user.id})[:-1]
    schema = ChangePassword(current_password='old', new_password='new')
    with pytest.raises(UserAuthDataServiceError):
        await auth_data_service.confirm_change_password(token, schema)


@pytest_mark_asyncio
async def test_confirm_change_password_token_expired(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository):
    user = User(id=1)
    token_handler = handler_factory.get_serializer_token_handler()
    token = token_handler.encode({'user_id': user.id})
    schema = ChangePassword(current_password='old', new_password='new')
    with freeze_time(datetime.now()+timedelta(seconds=config.URL_EXPIRE_TIME+3)):
        with pytest.raises(UserAuthDataServiceError):
            await auth_data_service.confirm_change_password(token, schema)


@pytest_mark_asyncio
async def test_confirm_change_password_user_is_none(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository, mock_serializer_handler: SerializerTokenHandler, mocker):
    mock_serializer_handler.validate_token.return_value = {'user_id': 1}
    mocker.patch('application.service.user.handler_factory.get_serializer_token_handler',
                 return_value=mock_serializer_handler)
    mock_user_repo.get_user.return_value = None
    schema = ChangePassword(current_password='old', new_password='new')
    with pytest.raises(UserAuthDataServiceError, match='Wrong url or expired'):
        await auth_data_service.confirm_change_password('token', schema)


@pytest_mark_asyncio
async def test_confirm_change_password_wrong_password(auth_data_service: UserAuthDataService, mock_user_repo: UserRepository, mock_serializer_handler: SerializerTokenHandler, mocker):
    mock_serializer_handler.validate_token.return_value = {'user_id': 1}
    mocker.patch('application.service.user.handler_factory.get_serializer_token_handler',
                 return_value=mock_serializer_handler)
    mock_user_repo.get_user.return_value = User(password='test')
    mocker.patch('application.service.user.check_password', return_value=False)
    schema = ChangePassword(current_password='old', new_password='new')
    with pytest.raises(UserAuthDataServiceError, match='Wrong password'):
        await auth_data_service.confirm_change_password('token', schema)
    mock_user_repo.update_user.assert_not_awaited()


"""testing user permission service"""


@pytest_mark_asyncio
async def test_check(permission_service: UserPermissionService, mock_user_repo: UserRepository):
    user = User(id=1, is_active=True)
    permission_service.perm_objs = [
        IsActivePermission()]
    user = permission_service.check(user)
    assert user == user


@pytest_mark_asyncio
async def test_permission_denied(permission_service: UserPermissionService):
    user = User(id=1, is_active=False)
    permission_service.perm_objs = [IsActivePermission()]
    with pytest.raises(UserPermissionServiceError, match='User is not active'):
        permission_service.check(user)
