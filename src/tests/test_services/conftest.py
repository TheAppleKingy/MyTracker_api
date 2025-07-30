import pytest

from domain.repositories.user_repository import AbstractUserRepository
from domain.repositories.task_repository import AbstractTaskRepository
from application.service.task import TaskService
from application.service.user import UserAuthDataService, UserAuthService, UserPermissionService


@pytest.fixture
def mock_task_repo(mocker):
    return mocker.Mock()


@pytest.fixture
def mock_user_repo(mocker):
    repo = mocker.Mock()
    repo.get_user = mocker.AsyncMock()
    repo.get_users_by = mocker.AsyncMock()
    repo.get_user_by_email = mocker.AsyncMock()
    repo.get_user_and_tasks = mocker.AsyncMock()
    repo.get_user_and_groups = mocker.AsyncMock()
    repo.create_user = mocker.AsyncMock()
    repo.update_user = mocker.AsyncMock()
    return repo


@pytest.fixture
def mock_jwt_handler(mocker):
    return mocker.Mock()


@pytest.fixture
def mock_serializer_handler(mocker):
    return mocker.Mock()


@pytest.fixture
def task_service(mock_task_repo: AbstractTaskRepository, mock_user_repo: AbstractUserRepository):
    return TaskService(mock_task_repo, mock_user_repo)


@pytest.fixture
def auth_data_service(mock_user_repo: AbstractUserRepository):
    return UserAuthDataService(mock_user_repo)


@pytest.fixture
def auth_service(mock_user_repo: AbstractUserRepository):
    return UserAuthService(mock_user_repo)


@pytest.fixture
def permission_service():
    return UserPermissionService([])
