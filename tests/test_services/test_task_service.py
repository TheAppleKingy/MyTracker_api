import pytest

from datetime import datetime, timedelta, timezone

from domain.entities.users import User
from domain.entities.tasks import Task
from domain.repositories.exceptions import TaskRepositoryError
from infra.db.repository.user_repo import UserRepository
from infra.db.repository.task_repo import TaskRepository
from application.service.task import TaskService
from application.service.exceptions import TaskServiceError
from application.dto.task_dto import TaskCreateForUser, TaskUpdateForUser


pytest_mark_asyncio = pytest.mark.asyncio


@pytest_mark_asyncio
async def test_check_is_root_for_user_success(task_service: TaskService, mock_task_repo: TaskRepository, mock_user_repo: UserRepository, mocker):
    task = Task(id=1, task_id=None, user_id=1)
    mock_user_repo.get_user_and_tasks = mocker.AsyncMock(
        return_value=User(id=1, tasks=[task]))
    mock_task_repo.get_task = mocker.AsyncMock(return_value=task)
    await task_service.check_is_root_for_user(1, 1)


@pytest_mark_asyncio
async def test_check_is_root_for_user_fail(task_service: TaskService, mock_task_repo: TaskRepository, mock_user_repo: UserRepository, mocker):
    user_task = Task(id=1, task_id=None)
    other_task = Task(id=2, task_id=None)
    mock_user_repo.get_user_and_tasks = mocker.AsyncMock(
        return_value=User(id=1, tasks=[user_task]))
    mock_task_repo.get_task = mocker.AsyncMock(return_value=other_task)
    with pytest.raises(TaskServiceError):
        await task_service.check_is_root_for_user(1, 2)


@pytest_mark_asyncio
async def test_get_full_trees(task_service: TaskService, mock_task_repo: TaskRepository, mocker):
    root1 = Task(id=1)
    root2 = Task(id=2)
    mock_task_repo.get_root_tasks = mocker.AsyncMock(
        return_value=[root1, root2])
    task_service.get_task_tree = mocker.AsyncMock(
        side_effect=lambda id, **kwargs: f"tree-{id}")
    result = await task_service.get_full_trees()
    assert result == ["tree-1", "tree-2"]


@pytest_mark_asyncio
async def test_get_task_tree(task_service: TaskService, mock_task_repo: TaskRepository, mocker):
    mock_task_repo.get_nested_tasks = mocker.AsyncMock(return_value="tree")
    result = await task_service.get_task_tree(1)
    assert result == "tree"


@pytest_mark_asyncio
async def test_get_tasks_trees(task_service: TaskService, mocker):
    task_service.get_task_tree = mocker.AsyncMock(
        side_effect=lambda tid, **_: f"tree-{tid}")
    result = await task_service.get_tasks_trees([1, 2])
    assert result == ["tree-1", "tree-2"]


@pytest_mark_asyncio
async def test_get_user_task_tree(task_service: TaskService, mocker):
    task_service.check_is_root_for_user = mocker.AsyncMock()
    task_service.get_task_tree = mocker.AsyncMock(return_value="tree")
    result = await task_service.get_user_task_tree(1, 1)
    assert result == "tree"


@pytest_mark_asyncio
async def test_get_user_tasks_trees(task_service: TaskService, mock_task_repo: TaskRepository, mocker):
    mock_task_repo.get_root_tasks_for_user = mocker.AsyncMock(
        return_value=[Task(id=1), Task(id=2)])
    task_service.get_tasks_trees = mocker.AsyncMock(
        return_value=["tree-1", "tree-2"])
    result = await task_service.get_user_tasks_trees(1)
    assert result == ["tree-1", "tree-2"]


@pytest_mark_asyncio
async def test_finish_task_success(task_service: TaskService, mock_task_repo: TaskRepository, mocker):
    task = Task(id=1, creation_date=datetime.now(timezone.utc),
                pass_date=None)
    subtask = Task(id=2, creation_date=datetime.now(timezone.utc),
                   pass_date=datetime.now(timezone.utc)+timedelta(days=2))
    task_service.get_task_tree = mocker.AsyncMock(return_value=[task, subtask])
    mock_task_repo.update_task = mocker.AsyncMock(return_value="ok")
    result = await task_service.finish_task(1)
    assert result == task


@pytest_mark_asyncio
async def test_finish_task_fail_unfinished_subtasks(task_service: TaskService, mock_task_repo: TaskRepository, mocker):
    task = Task(id=1, title='t1', creation_date=datetime.now(),
                deadline=datetime.now()+timedelta(days=2))
    unfinished = Task(id=2, title='t2',
                      creation_date=datetime.now(), pass_date=None)
    task_service.get_task_tree = mocker.AsyncMock(
        return_value=[task, unfinished])
    mock_task_repo.get_nested_tasks = mocker.AsyncMock()
    with pytest.raises(TaskServiceError) as exc_info:
        await task_service.finish_task(1)
    assert "not finished subtasks" in str(exc_info.value)


@pytest_mark_asyncio
async def test_add_task_to_user(task_service: TaskService, mock_task_repo: TaskRepository, mocker):
    schema = TaskCreateForUser(
        title="Test", task_id=None, description='test desc', creation_date=datetime.now(), deadline=datetime.now()+timedelta(days=2))
    mock_task_repo.create_task = mocker.AsyncMock(return_value=Task(id=1))
    task_service.get_task_tree = mocker.AsyncMock(return_value="created")
    result = await task_service.add_task_to_user(1, schema)
    assert result == "created"


@pytest_mark_asyncio
async def test_update_task_for_user_success(task_service: TaskService, mock_task_repo: TaskRepository, mocker):
    updated = Task(id=1, user_id=1, title="Updated")
    mock_task_repo.get_nested_tasks = mocker.AsyncMock(
        return_value=updated)
    mock_task_repo.update_task = mocker.AsyncMock(
        return_value=Task(id=1, title='Updated'))
    schema = TaskUpdateForUser(title="Updated")
    result = await task_service.update_task_for_user(1, 1, schema)
    assert result == updated


@pytest_mark_asyncio
async def test_update_task_for_user_fail(task_service: TaskService, mock_task_repo: TaskRepository, mocker):
    mock_task_repo.get_nested_tasks = mocker.AsyncMock(
        side_effect=TaskRepositoryError('Task does not exist'))
    schema = TaskUpdateForUser(title="Updated")
    with pytest.raises(TaskServiceError, match='Task does not exist'):
        await task_service.update_task_for_user(1, 1, schema)


@pytest_mark_asyncio
async def test_finish_task_for_user_success(task_service: TaskService, mock_task_repo: TaskRepository, mocker):
    task = Task(id=1, user_id=1)
    mock_task_repo.get_task = mocker.AsyncMock(return_value=task)
    task_service.finish_task = mocker.AsyncMock(return_value="finished")
    result = await task_service.finish_task_for_user(1, 1)
    assert result == "finished"


@pytest_mark_asyncio
async def test_finish_task_for_user_fail(task_service: TaskService, mock_task_repo: TaskRepository, mocker):
    task = Task(id=1, title='t1', user_id=999)
    mock_task_repo.get_task = mocker.AsyncMock(return_value=task)
    task_service.finish_task = mocker.AsyncMock()
    with pytest.raises(TaskServiceError):
        await task_service.finish_task_for_user(2, 1)
