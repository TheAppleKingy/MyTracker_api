import pytest
import asyncio

from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta

from src.application.use_cases.tasks import *
from src.application.use_cases.exceptions import TaskAlreadyFinishedError, UndefinedTaskError
from src.application.dto.task import TaskCreateDTO, TaskUpdateDTO
from src.domain.entities import Task
from src.domain.entities.exceptions import UnfinishedTaskError
from src.domain.services.task import TaskProducerService, MAX_DEPTH, TaskPlannerManagerService
from src.domain.services.exceptions import MaxDepthError, ParentFinishedError, InvalidDeadlineError


def test_execute_create_root_task_success():
    """Test successful creation of root task (no parent)"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    user_id = 42
    dto = TaskCreateDTO(
        title="Test Task",
        deadline=datetime.now(timezone.utc) + timedelta(days=1),
        parent_id=None,
        description="Test description"
    )

    # Create a mock for the context manager
    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit

    create_use_case = CreateTask(mock_uow, mock_task_repo)

    # Act
    result = asyncio.run(create_use_case.execute(user_id, dto))

    # Assert
    # Should not call get_with_parents since parent_id is None
    mock_task_repo.get_with_parents.assert_not_called()
    # Should save a task
    mock_uow.save.assert_called_once()
    saved_task = mock_uow.save.call_args[0][0]
    assert isinstance(saved_task, Task)
    assert saved_task.title == dto.title
    assert saved_task.deadline == dto.deadline
    assert saved_task.user_id == user_id
    assert saved_task.description == dto.description
    assert saved_task.parent is None


def test_execute_create_subtask_success():
    """Test successful creation of subtask with valid parent"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    user_id = 42
    parent_id = 123
    dto = TaskCreateDTO(
        title="Subtask",
        deadline=datetime.now(timezone.utc) + timedelta(days=1),
        parent_id=parent_id,
        description="Subtask description"
    )

    # Mock parent task
    mock_parent = Mock()
    mock_parent.get_depth.return_value = 1  # Within max depth
    mock_parent.is_done = False
    mock_parent.deadline = datetime.now(timezone.utc) + timedelta(days=2)  # Later than subtask

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parents.return_value = mock_parent

    create_use_case = CreateTask(mock_uow, mock_task_repo)

    # Act
    result = asyncio.run(create_use_case.execute(user_id, dto))

    # Assert
    mock_task_repo.get_with_parents.assert_called_once_with(parent_id)
    mock_uow.save.assert_called_once()
    saved_task = mock_uow.save.call_args[0][0]
    assert saved_task.parent is mock_parent


def test_execute_parent_not_found():
    """Test creation fails when parent task doesn't exist"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    user_id = 42
    parent_id = 999
    dto = TaskCreateDTO(
        title="Task",
        deadline=datetime.now(timezone.utc) + timedelta(days=1),
        parent_id=parent_id,
        description=""
    )

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parents.return_value = None

    create_use_case = CreateTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(UndefinedTaskError) as exc_info:
        asyncio.run(create_use_case.execute(user_id, dto))

    assert "Unable to bind to unexistent parent task" in str(exc_info.value)
    mock_task_repo.get_with_parents.assert_called_once_with(parent_id)
    mock_uow.save.assert_not_called()


def test_execute_parent_exceeds_max_depth():
    """Test creation fails when parent is at max depth"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    user_id = 42
    parent_id = 123
    dto = TaskCreateDTO(
        title="Subtask",
        deadline=datetime.now(timezone.utc) + timedelta(days=1),
        parent_id=parent_id,
        description=""
    )

    # Mock parent at max depth
    mock_parent = Mock()
    mock_parent.get_depth.return_value = MAX_DEPTH  # At max depth
    mock_parent.is_done = False
    mock_parent.deadline = datetime.now(timezone.utc) + timedelta(days=2)

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parents.return_value = mock_parent

    create_use_case = CreateTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(MaxDepthError) as exc_info:
        asyncio.run(create_use_case.execute(user_id, dto))

    assert f"Depth of task tree couldn't be more than {MAX_DEPTH}" in str(exc_info.value)
    mock_task_repo.get_with_parents.assert_called_once_with(parent_id)
    mock_uow.save.assert_not_called()


def test_execute_parent_is_done():
    """Test creation fails when parent task is already done"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    user_id = 42
    parent_id = 123
    dto = TaskCreateDTO(
        title="Subtask",
        deadline=datetime.now(timezone.utc) + timedelta(days=1),
        parent_id=parent_id,
        description=""
    )

    # Mock parent that's done
    mock_parent = Mock()
    mock_parent.get_depth.return_value = 1
    mock_parent.is_done = True  # Parent is finished!
    mock_parent.deadline = datetime.now(timezone.utc) + timedelta(days=2)

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parents.return_value = mock_parent

    create_use_case = CreateTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(ParentFinishedError) as exc_info:
        asyncio.run(create_use_case.execute(user_id, dto))

    assert "Unable to create subtasks of fnished parent task" in str(exc_info.value)
    mock_task_repo.get_with_parents.assert_called_once_with(parent_id)
    mock_uow.save.assert_not_called()


def test_execute_subtask_deadline_exceeds_parent():
    """Test creation fails when subtask deadline is later than parent's"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    user_id = 42
    parent_id = 123
    dto = TaskCreateDTO(
        title="Subtask",
        deadline=datetime.now(timezone.utc) + timedelta(days=3),  # Later than parent
        parent_id=parent_id,
        description=""
    )

    # Mock parent with earlier deadline
    mock_parent = Mock()
    mock_parent.get_depth.return_value = 1
    mock_parent.is_done = False
    mock_parent.deadline = datetime.now(timezone.utc) + timedelta(days=2)  # Earlier!

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parents.return_value = mock_parent

    create_use_case = CreateTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(InvalidDeadlineError) as exc_info:
        asyncio.run(create_use_case.execute(user_id, dto))

    assert "Deadline of creating task cannot be later than deadline of parent task" in str(
        exc_info.value)
    mock_task_repo.get_with_parents.assert_called_once_with(parent_id)
    mock_uow.save.assert_not_called()


def test_execute_past_deadline():
    """Test creation fails when deadline is in the past"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    user_id = 42
    dto = TaskCreateDTO(
        title="Task",
        deadline=datetime.now(timezone.utc) - timedelta(minutes=1),  # Past deadline
        parent_id=None,
        description=""
    )

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit

    create_use_case = CreateTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(InvalidDeadlineError) as exc_info:
        asyncio.run(create_use_case.execute(user_id, dto))

    assert "Deadline cannot be less or equal than now" in str(exc_info.value)
    mock_task_repo.get_with_parents.assert_not_called()
    mock_uow.save.assert_not_called()


def test_execute_current_deadline():
    """Test creation fails when deadline is current time"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    user_id = 42
    current_time = datetime.now(timezone.utc)
    dto = TaskCreateDTO(
        title="Task",
        deadline=current_time,  # Current time
        parent_id=None,
        description=""
    )

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit

    create_use_case = CreateTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(InvalidDeadlineError) as exc_info:
        asyncio.run(create_use_case.execute(user_id, dto))

    assert "Deadline cannot be less or equal than now" in str(exc_info.value)
    mock_task_repo.get_with_parents.assert_not_called()
    mock_uow.save.assert_not_called()


def test_execute_repository_raises_exception():
    """Test behavior when repository raises an exception"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    user_id = 42
    parent_id = 123
    dto = TaskCreateDTO(
        title="Task",
        deadline=datetime.now(timezone.utc) + timedelta(days=1),
        parent_id=parent_id,
        description=""
    )

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parents.side_effect = Exception("Database error")

    create_use_case = CreateTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        asyncio.run(create_use_case.execute(user_id, dto))

    assert "Database error" in str(exc_info.value)
    mock_task_repo.get_with_parents.assert_called_once_with(parent_id)
    mock_uow.save.assert_not_called()


def test_execute_task_producer_service_used():
    """Test that TaskProducerService is instantiated and used"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    user_id = 42
    dto = TaskCreateDTO(
        title="Test Task",
        deadline=datetime.now(timezone.utc) + timedelta(days=1),
        parent_id=None,
        description=""
    )

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit

    create_use_case = CreateTask(mock_uow, mock_task_repo)

    # Act
    with patch.object(TaskProducerService, 'create_task') as mock_create_task:
        mock_created_task = Mock()
        mock_create_task.return_value = mock_created_task

        asyncio.run(create_use_case.execute(user_id, dto))

        # Assert
        mock_create_task.assert_called_once_with(
            dto.title,
            dto.deadline,
            user_id,
            dto.description,
            None,  # parent
        )
        mock_uow.save.assert_called_once_with(mock_created_task)


def test_execute_update_title_only():
    """Test updating only the title"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123
    dto = TaskUpdateDTO(
        title="Updated Title",
        description=None,
        deadline=None
    )

    # Mock task
    mock_task = Mock()
    mock_task.title = "Original Title"
    mock_task.description = "Original Description"

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False  # Don't suppress exceptions

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parent_and_subs.return_value = mock_task

    update_use_case = UpdateTask(mock_uow, mock_task_repo)

    # Act
    result = asyncio.run(update_use_case.execute(task_id, dto))

    # Assert
    mock_task_repo.get_with_parent_and_subs.assert_called_once_with(task_id)
    assert mock_task.title == "Updated Title"
    assert mock_task.description == "Original Description"  # Unchanged


def test_execute_update_description_only():
    """Test updating only the description"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123
    dto = TaskUpdateDTO(
        title=None,
        description="Updated Description",
        deadline=None
    )

    mock_task = Mock()
    mock_task.title = "Original Title"
    mock_task.description = "Original Description"

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parent_and_subs.return_value = mock_task

    update_use_case = UpdateTask(mock_uow, mock_task_repo)

    # Act
    result = asyncio.run(update_use_case.execute(task_id, dto))

    # Assert
    mock_task_repo.get_with_parent_and_subs.assert_called_once_with(task_id)
    assert mock_task.title == "Original Title"  # Unchanged
    assert mock_task.description == "Updated Description"


def test_execute_update_deadline_only():
    """Test updating only the deadline"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123
    new_deadline = datetime.now(timezone.utc) + timedelta(days=5)
    dto = TaskUpdateDTO(
        title=None,
        description=None,
        deadline=new_deadline,
    )

    mock_task = Mock()
    mock_task.title = "Original Title"
    mock_task.description = "Original Description"
    mock_task._deadline = datetime.now(timezone.utc) + timedelta(days=1)

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parent_and_subs.return_value = mock_task

    update_use_case = UpdateTask(mock_uow, mock_task_repo)

    # Act
    with patch.object(TaskPlannerManagerService, 'set_deadline') as mock_set_deadline:
        asyncio.run(update_use_case.execute(task_id, dto))

        # Assert
        mock_task_repo.get_with_parent_and_subs.assert_called_once_with(task_id)
        mock_set_deadline.assert_called_once_with(new_deadline)
        assert mock_task.title == "Original Title"
        assert mock_task.description == "Original Description"


def test_execute_update_all_fields():
    """Test updating all fields at once"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123
    new_deadline = datetime.now(timezone.utc) + timedelta(days=5)
    dto = TaskUpdateDTO(
        title="New Title",
        description="New Description",
        deadline=new_deadline
    )

    mock_task = Mock()
    mock_task.title = "Old Title"
    mock_task.description = "Old Description"
    mock_task._deadline = datetime.now(timezone.utc) + timedelta(days=1)

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parent_and_subs.return_value = mock_task

    update_use_case = UpdateTask(mock_uow, mock_task_repo)

    # Act
    with patch.object(TaskPlannerManagerService, 'set_deadline') as mock_set_deadline:
        asyncio.run(update_use_case.execute(task_id, dto))

        # Assert
        mock_task_repo.get_with_parent_and_subs.assert_called_once_with(task_id)
        assert mock_task.title == "New Title"
        assert mock_task.description == "New Description"
        mock_set_deadline.assert_called_once_with(new_deadline)


def test_execute_manager_raises_invalid_deadline():
    """Test that InvalidDeadlineError from manager propagates"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123
    invalid_deadline = datetime.now(timezone.utc) - timedelta(days=1)  # Past
    dto = TaskUpdateDTO(
        title=None,
        description=None,
        deadline=invalid_deadline
    )

    mock_task = Mock()
    mock_task.title = "Task"
    mock_task.description = "Description"

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False  # Important: don't suppress exceptions

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parent_and_subs.return_value = mock_task

    update_use_case = UpdateTask(mock_uow, mock_task_repo)

    # Mock TaskPlannerManagerService to raise error
    with patch.object(TaskPlannerManagerService, 'set_deadline',
                      side_effect=InvalidDeadlineError("Deadline cannot be in past")):
        # Act & Assert
        with pytest.raises(InvalidDeadlineError) as exc_info:
            asyncio.run(update_use_case.execute(task_id, dto))

        assert "Deadline cannot be in past" in str(exc_info.value)
        mock_task_repo.get_with_parent_and_subs.assert_called_once_with(task_id)


def test_execute_no_fields_to_update():
    """Test update with empty DTO (no changes)"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123
    dto = TaskUpdateDTO(
        title=None,
        description=None,
        deadline=None
    )

    mock_task = Mock()
    mock_task.title = "Original Title"
    mock_task.description = "Original Description"
    mock_task._deadline = datetime.now(timezone.utc) + timedelta(days=1)

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parent_and_subs.return_value = mock_task

    update_use_case = UpdateTask(mock_uow, mock_task_repo)

    # Act
    result = asyncio.run(update_use_case.execute(task_id, dto))

    # Assert
    mock_task_repo.get_with_parent_and_subs.assert_called_once_with(task_id)
    assert mock_task.title == "Original Title"
    assert mock_task.description == "Original Description"


def test_execute_partial_updates():
    """Test various partial update combinations"""
    test_cases = [
        # (title, description, deadline should be set)
        ("New Title", None, None),
        (None, "New Desc", None),
        (None, None, datetime.now(timezone.utc) + timedelta(days=3)),
        ("New Title", "New Desc", None),
        (None, "New Desc", datetime.now(timezone.utc) + timedelta(days=3)),
        ("New Title", None, datetime.now(timezone.utc) + timedelta(days=3)),
    ]

    for title, description, deadline in test_cases:
        # Arrange
        mock_uow = Mock()
        mock_task_repo = AsyncMock()

        task_id = 123
        dto = TaskUpdateDTO(
            title=title,
            description=description,
            deadline=deadline
        )

        mock_task = Mock()
        mock_task.title = "Old Title"
        mock_task.description = "Old Desc"
        mock_task._deadline = datetime.now(timezone.utc) + timedelta(days=1)

        async def aenter(self):
            return mock_uow

        async def aexit(self, exc_type, exc_val, exc_tb):
            return False

        mock_uow.__aenter__ = aenter
        mock_uow.__aexit__ = aexit
        mock_task_repo.get_with_parent_and_subs.return_value = mock_task

        update_use_case = UpdateTask(mock_uow, mock_task_repo)

        # Act
        with patch.object(TaskPlannerManagerService, 'set_deadline') as mock_set_deadline:
            asyncio.run(update_use_case.execute(task_id, dto))

            # Assert
            mock_task_repo.get_with_parent_and_subs.assert_called_once_with(task_id)

            if title:
                assert mock_task.title == title
            else:
                assert mock_task.title == "Old Title"

            if description:
                assert mock_task.description == description
            else:
                assert mock_task.description == "Old Desc"

            if deadline:
                mock_set_deadline.assert_called_once_with(deadline)
            else:
                mock_set_deadline.assert_not_called()

        # Reset for next iteration
        mock_uow.reset_mock()
        mock_task_repo.reset_mock()


def test_execute_uow_aexit_returns_false_on_exception():
    """Test that uow.__aexit__ returns False when there's an exception"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123
    dto = TaskUpdateDTO(
        title="New Title",
        description=None,
        deadline=None
    )

    mock_task = Mock()
    mock_task.title = "Old Title"
    mock_task.description = "Old Desc"

    # Track if aexit was called with exception
    aexit_called_with_exception = False

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        nonlocal aexit_called_with_exception
        if exc_type is not None:
            aexit_called_with_exception = True
        return False  # Important: propagate exceptions

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_with_parent_and_subs.side_effect = Exception("DB error")

    update_use_case = UpdateTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        asyncio.run(update_use_case.execute(task_id, dto))

    assert "DB error" in str(exc_info.value)
    assert aexit_called_with_exception == True


def test_finish_task_success():
    """Test successful completion of a task with all subtasks done"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123

    # Create actual Task objects
    subtask1 = Task("Subtask 1", datetime.now(timezone.utc) + timedelta(days=1), user_id=1, description="")
    subtask1._pass_date = datetime.now(timezone.utc)  # Already done

    subtask2 = Task("Subtask 2", datetime.now(timezone.utc) + timedelta(days=2), user_id=1, description="")
    subtask2._pass_date = datetime.now(timezone.utc)  # Already done

    task = Task("Main Task", datetime.now(timezone.utc) + timedelta(days=3), user_id=1, description="")
    task.subtasks = [subtask1, subtask2]

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_task_tree.return_value = task

    finish_use_case = FinishTask(mock_uow, mock_task_repo)

    # Act
    result = asyncio.run(finish_use_case.execute(task_id))

    # Assert
    mock_task_repo.get_task_tree.assert_called_once_with(task_id)
    assert task.is_done == True
    assert task._pass_date is not None


def test_finish_task_already_finished():
    """Test finishing an already finished task raises error"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123

    task = Task("Main Task", datetime.now(timezone.utc) + timedelta(days=1), user_id=1, description="")
    task._pass_date = datetime.now(timezone.utc)  # Already done

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_task_tree.return_value = task

    finish_use_case = FinishTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(TaskAlreadyFinishedError) as exc_info:
        asyncio.run(finish_use_case.execute(task_id))

    assert "Task already finished" in str(exc_info.value)
    mock_task_repo.get_task_tree.assert_called_once_with(task_id)


def test_finish_task_with_unfinished_subtasks():
    """Test finishing a task with unfinished subtasks raises error"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123

    # Create task with unfinished subtask
    subtask = Task("Subtask", datetime.now(timezone.utc) + timedelta(days=1), user_id=1, description="")
    # Not marked as done

    task = Task("Main Task", datetime.now(timezone.utc) + timedelta(days=2), user_id=1, description="")
    task.subtasks = [subtask]

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_task_tree.return_value = task

    finish_use_case = FinishTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(UnfinishedTaskError) as exc_info:
        asyncio.run(finish_use_case.execute(task_id))

    assert "Unable finish task while subtasks not fininshed" in str(exc_info.value)
    mock_task_repo.get_task_tree.assert_called_once_with(task_id)
    assert task.is_done == False  # Should not be marked as done


def test_finish_task_nested_subtasks_unfinished():
    """Test finishing task with nested unfinished subtasks"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123

    # Create nested structure: task -> subtask -> nested_subtask (unfinished)
    nested_subtask = Task("Nested Subtask", datetime.now(
        timezone.utc) + timedelta(days=1), user_id=1, description="")
    # Not marked as done

    subtask = Task("Subtask", datetime.now(timezone.utc) + timedelta(days=2), user_id=1, description="")
    subtask._pass_date = datetime.now(timezone.utc)  # Parent is done
    subtask.subtasks = [nested_subtask]

    task = Task("Main Task", datetime.now(timezone.utc) + timedelta(days=3), user_id=1, description="")
    task.subtasks = [subtask]

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_task_tree.return_value = task

    finish_use_case = FinishTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(UnfinishedTaskError) as exc_info:
        asyncio.run(finish_use_case.execute(task_id))

    assert "Unable finish task while subtasks not fininshed" in str(exc_info.value)
    mock_task_repo.get_task_tree.assert_called_once_with(task_id)
    assert task.is_done == False


def test_force_finish_task_success():
    """Test force finishing a task regardless of subtasks"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123

    # Create task with unfinished subtasks (should still work with force)
    subtask1 = Task("Subtask 1", datetime.now(timezone.utc) + timedelta(days=1), user_id=1, description="")
    # Not marked as done

    subtask2 = Task("Subtask 2", datetime.now(timezone.utc) + timedelta(days=2), user_id=1, description="")
    subtask2._pass_date = datetime.now(timezone.utc)  # Already done

    task = Task("Main Task", datetime.now(timezone.utc) + timedelta(days=3), user_id=1, description="")
    task.subtasks = [subtask1, subtask2]

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_task_tree.return_value = task

    force_finish_use_case = ForceFinishTask(mock_uow, mock_task_repo)

    # Act
    result = asyncio.run(force_finish_use_case.execute(task_id))

    # Assert
    mock_task_repo.get_task_tree.assert_called_once_with(task_id)
    assert task.is_done == True
    assert task._pass_date is not None
    # All subtasks should be force marked as done
    assert subtask1.is_done == True
    assert subtask2.is_done == True  # Was already done, still True


def test_force_finish_task_already_finished():
    """Test force finishing an already finished task raises error"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123

    task = Task("Main Task", datetime.now(timezone.utc) + timedelta(days=1), user_id=1, description="")
    task._pass_date = datetime.now(timezone.utc)  # Already done

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_task_tree.return_value = task

    force_finish_use_case = ForceFinishTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(TaskAlreadyFinishedError) as exc_info:
        asyncio.run(force_finish_use_case.execute(task_id))

    assert "Task already finished" in str(exc_info.value)
    mock_task_repo.get_task_tree.assert_called_once_with(task_id)


def test_force_finish_task_nested_subtasks():
    """Test force finishing propagates to nested subtasks"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123

    # Create deep nested structure
    deep_nested = Task("Deep Nested", datetime.now(timezone.utc) + timedelta(days=1), user_id=1, description="")

    nested = Task("Nested", datetime.now(timezone.utc) + timedelta(days=2), user_id=1, description="")
    nested.subtasks = [deep_nested]

    subtask = Task("Subtask", datetime.now(timezone.utc) + timedelta(days=3), user_id=1, description="")
    subtask.subtasks = [nested]

    task = Task("Main Task", datetime.now(timezone.utc) + timedelta(days=4), user_id=1, description="")
    task.subtasks = [subtask]

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_task_tree.return_value = task

    force_finish_use_case = ForceFinishTask(mock_uow, mock_task_repo)

    # Act
    result = asyncio.run(force_finish_use_case.execute(task_id))

    # Assert
    mock_task_repo.get_task_tree.assert_called_once_with(task_id)
    assert task.is_done == True
    assert subtask.is_done == True
    assert nested.is_done == True
    assert deep_nested.is_done == True


def test_finish_task_no_subtasks():
    """Test finishing a task with no subtasks"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123

    task = Task("Main Task", datetime.now(timezone.utc) + timedelta(days=1), user_id=1, description="")
    task.subtasks = []  # No subtasks

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_task_tree.return_value = task

    finish_use_case = FinishTask(mock_uow, mock_task_repo)

    # Act
    result = asyncio.run(finish_use_case.execute(task_id))

    # Assert
    mock_task_repo.get_task_tree.assert_called_once_with(task_id)
    assert task.is_done == True
    assert task._pass_date is not None


def test_force_finish_task_no_subtasks():
    """Test force finishing a task with no subtasks"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123

    task = Task("Main Task", datetime.now(timezone.utc) + timedelta(days=1), user_id=1, description="")
    task.subtasks = []  # No subtasks

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_task_tree.return_value = task

    force_finish_use_case = ForceFinishTask(mock_uow, mock_task_repo)

    # Act
    result = asyncio.run(force_finish_use_case.execute(task_id))

    # Assert
    mock_task_repo.get_task_tree.assert_called_once_with(task_id)
    assert task.is_done == True
    assert task._pass_date is not None


def test_uow_exception_propagation():
    """Test that exceptions from mark_as_done propagate through uow"""
    # Arrange
    mock_uow = Mock()
    mock_task_repo = AsyncMock()

    task_id = 123

    # Create a task that will raise an exception when mark_as_done is called
    subtask = Task("Subtask", datetime.now(timezone.utc) + timedelta(days=1), user_id=1, description="")
    # Not done, so mark_as_done will raise UnfinishedTaskError

    task = Task("Main Task", datetime.now(timezone.utc) + timedelta(days=2), user_id=1, description="")
    task.subtasks = [subtask]

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        # Should return False to propagate exception
        return False

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_task_repo.get_task_tree.return_value = task

    finish_use_case = FinishTask(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(UnfinishedTaskError) as exc_info:
        asyncio.run(finish_use_case.execute(task_id))

    assert "Unable finish task while subtasks not fininshed" in str(exc_info.value)
    mock_task_repo.get_task_tree.assert_called_once_with(task_id)
    assert task.is_done == False
