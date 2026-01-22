import pytest
import httpx

import config

from datetime import datetime, timedelta

from freezegun import freeze_time
from domain.entities.users import User
from infra.db.repository.user_repo import UserRepository
from infra.security.token.factory import TokenHandlerFactory
from infra.security.password_utils import check_password
from application.dto.users_dto import UserView
from application.service.exceptions import UserAuthServiceError


pytest_mark_asyncio = pytest.mark.asyncio
urls = {
    'profile': {
        'login': '/api/profile/login',
        'logout': '/api/profile/logout',
        'registration_request': '/api/profile/request/registration',
        'registration_confirm': '/api/profile/confirm/registration/{token}',
        'change_password_request': '/api/profile/request/change_password',
        'change_password_confirm': '/api/profile/confirm/change_password/{token}',
    },
    'user_api': {
        'get_users': '/api/users',
        'create_user': '/api/users',
        'get_user': '/api/users/{}',
        'update_user': '/api/users/{}',
        'delete_user': '/api/users/{}'

    },
    'groups_api': {
        'get_groups': '/api/groups',
        'add_users': '/api/groups/{}/add_users',
        'exclude_users': '/api/groups/{}/exclude_users'
    }
}


"""test registration routs"""


@pytest_mark_asyncio
async def test_registration_request(simple_client: httpx.AsyncClient, user_repo: UserRepository, mocker):
    data = {
        'tg_name': 'new_tg',
        'email': 'user@mail.ru',
        'password': 'test-password'
    }
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    response = await simple_client.post(urls['profile']['registration_request'], json=data)
    assert response.status_code == 200
    registered = await user_repo.get_user_by_email(data['email'])
    mock_send_mail.assert_called_once()
    assert registered is not None
    assert not registered.is_active
    assert response.json() == {
        'detail': 'we sent email on your mail for confirm registration'}


@pytest_mark_asyncio
async def test_registration_request_fail(simple_client: httpx.AsyncClient, simple_user: User):
    data = {
        'tg_name': simple_user.tg_name,
        'email': 'user@mail.ru',
        'password': 'test-password'
    }
    response = await simple_client.post(urls['profile']['registration_request'], json=data)
    assert response.status_code == 400
    assert response.json() == {
        'detail': f'User with tg_name {simple_user.tg_name} already exists'}


@pytest_mark_asyncio
async def test_confirm_registration(simple_client: httpx.AsyncClient, user_repo: UserRepository,  mocker):
    data = {
        'tg_name': 'new_tg',
        'email': 'user@mail.ru',
        'password': 'test-password'
    }
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    await simple_client.post(urls['profile']['registration_request'], json=data)
    registered = await user_repo.get_user_by_email(data['email'])
    assert not registered.is_active
    args, kwargs = mock_send_mail.call_args
    url = args[1]
    token = url.split('/')[-1]
    response = await simple_client.get(urls['profile']['registration_confirm'].format(token=token))
    assert response.status_code == 200
    assert response.json() == {'detail': 'registration confirmed!'}
    assert registered.is_active


@pytest_mark_asyncio
async def test_confirm_registration_invalid_token(simple_client: httpx.AsyncClient, user_repo: UserRepository,  mocker):
    data = {
        'tg_name': 'new_tg',
        'email': 'user@mail.ru',
        'password': 'test-password'
    }
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    await simple_client.post(urls['profile']['registration_request'], json=data)
    registered = await user_repo.get_user_by_email(data['email'])
    args, kwargs = mock_send_mail.call_args
    url = args[1]
    token = url.split('/')[-1][:-1]
    response = await simple_client.get(urls['profile']['registration_confirm'].format(token=token))
    assert response.status_code == 400
    assert response.json() == {'detail': 'Wrong url or expired'}
    assert not registered.is_active


@pytest_mark_asyncio
async def test_confirm_registration_token_expired(simple_client: httpx.AsyncClient, user_repo: UserRepository,  mocker):
    data = {
        'tg_name': 'new_tg',
        'email': 'user@mail.ru',
        'password': 'test-password'
    }
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    await simple_client.post(urls['profile']['registration_request'], json=data)
    registered = await user_repo.get_user_by_email(data['email'])
    args, kwargs = mock_send_mail.call_args
    url = args[1]
    token = url.split('/')[-1]
    with freeze_time(datetime.now()+timedelta(seconds=config.URL_EXPIRE_TIME+3)):
        response = await simple_client.get(urls['profile']['registration_confirm'].format(token=token))
        assert response.status_code == 400
        assert response.json() == {'detail': 'Wrong url or expired'}
        assert not registered.is_active


@pytest_mark_asyncio
async def test_confirm_registration_already_active(simple_client: httpx.AsyncClient, user_repo: UserRepository,  mocker):
    data = {
        'tg_name': 'new_tg',
        'email': 'user@mail.ru',
        'password': 'test-password'
    }
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    await simple_client.post(urls['profile']['registration_request'], json=data)
    registered = await user_repo.get_user_by_email(data['email'])
    registered.is_active = True
    await user_repo.session.commit()
    args, kwargs = mock_send_mail.call_args
    url = args[1]
    token = url.split('/')[-1]
    response = await simple_client.get(urls['profile']['registration_confirm'].format(token=token))
    assert response.status_code == 400
    assert response.json() == {'detail': 'Your account is already activated'}


"""test change password routs"""


@pytest_mark_asyncio
async def test_change_password_request(simple_client: httpx.AsyncClient, user_repo: UserRepository,  mocker):
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    response = await simple_client.get(urls['profile']['change_password_request'])
    assert response.status_code == 200
    assert response.json() == {
        'detail': 'we sent email on your mail for confirm change password'}
    mock_send_mail.assert_called_once()


@pytest_mark_asyncio
async def test_change_password_confirm(simple_client: httpx.AsyncClient, simple_user: User,  user_repo: UserRepository,  mocker):
    data = {
        'current_password': 'test_password',
        'new_password': 'new'
    }
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    await simple_client.get(urls['profile']['change_password_request'])
    args, kwargs = mock_send_mail.call_args
    url = args[1]
    token = url.split('/')[-1]
    response = await simple_client.post(urls['profile']['change_password_confirm'].format(token=token), json=data)
    assert response.status_code == 200
    assert response.json() == {'detail': 'password was change successfully'}
    assert check_password('new', simple_user.password)


@pytest_mark_asyncio
async def test_change_password_confirm_invalid_token(simple_client: httpx.AsyncClient, simple_user: User,  user_repo: UserRepository,  mocker):
    data = {
        'current_password': 'test_password',
        'new_password': 'new'
    }
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    await simple_client.get(urls['profile']['change_password_request'])
    args, kwargs = mock_send_mail.call_args
    url = args[1]
    token = url.split('/')[-1][:-1]
    response = await simple_client.post(urls['profile']['change_password_confirm'].format(token=token), json=data)
    assert response.status_code == 400
    assert response.json() == {'detail': 'Wrong url or expired'}
    assert not check_password('new', simple_user.password)


@pytest_mark_asyncio
async def test_change_password_confirm_token_expired(simple_client: httpx.AsyncClient, simple_user: User,  user_repo: UserRepository,  mocker):
    data = {
        'current_password': 'test_password',
        'new_password': 'new'
    }
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    await simple_client.get(urls['profile']['change_password_request'])
    args, kwargs = mock_send_mail.call_args
    url = args[1]
    token = url.split('/')[-1]
    with freeze_time(datetime.now()+timedelta(seconds=config.URL_EXPIRE_TIME+3)):
        response = await simple_client.post(urls['profile']['change_password_confirm'].format(token=token), json=data)
        assert response.status_code == 400
        assert response.json() == {'detail': 'Wrong url or expired'}
        assert not check_password('new', simple_user.password)


@pytest_mark_asyncio
async def test_change_password_confirm_wrong_password(simple_client: httpx.AsyncClient, simple_user: User,  user_repo: UserRepository,  mocker):
    data = {
        'current_password': 'test_passwor',
        'new_password': 'new'
    }
    mock_send_mail = mocker.patch('application.service.user.send_mail.delay')
    await simple_client.get(urls['profile']['change_password_request'])
    args, kwargs = mock_send_mail.call_args
    url = args[1]
    token = url.split('/')[-1]
    response = await simple_client.post(urls['profile']['change_password_confirm'].format(token=token), json=data)
    assert response.status_code == 400
    assert response.json() == {'detail': 'Wrong password'}
    assert not check_password('new', simple_user.password)


"""test login"""


@pytest_mark_asyncio
async def test_login(client: httpx.AsyncClient, simple_user: User):
    response = await client.post(urls['profile']['login'], json={'email': simple_user.email, 'password': 'test_password'})
    assert response.status_code == 200
    assert response.json() == {'detail': 'logged in'}
    token = client.cookies.get('token', None)
    assert token is not None
    jwt_handler = TokenHandlerFactory.get_jwt_handler()
    payload = jwt_handler.decode(token)
    assert payload['user_id'] == simple_user.id


@pytest_mark_asyncio
async def test_login_fail_pas(client: httpx.AsyncClient, simple_user: User):
    data = {
        'email': simple_user.email,
        'password': 'test_passwor'
    }
    response = await client.post(urls['profile']['login'], json=data)
    assert response.status_code == 400
    assert response.json() == {'detail': 'Wrong password'}


@pytest_mark_asyncio
async def test_login_fail_email(client: httpx.AsyncClient):
    data = {
        'email': 'dasdasd',
        'password': 'test_password'
    }
    response = await client.post(urls['profile']['login'], json=data)
    assert response.status_code == 400
    assert response.json() == {
        'detail': f'Unable to find user with email {data["email"]}'}


"""test logout"""


@pytest_mark_asyncio
async def test_logout(simple_client: httpx.AsyncClient):
    response = await simple_client.post(urls['profile']['logout'])
    assert response.status_code == 200
    assert response.json() == {
        'detail': 'logged out'
    }
    token = simple_client.cookies.get('token', None)
    assert token is None


@pytest_mark_asyncio
async def test_logout_fail(client: httpx.AsyncClient):
    response = await client.post(urls['profile']['logout'])
    assert response.status_code == 401
    assert response.json() == {'detail': 'token was not provide'}
