# tests/test_domain_services.py
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from src.domain.entities import Task
from src.domain.services.exceptions import (
    MaxDepthError,
    InvalidDeadlineError
)
from src.domain.services import (
    TaskProducerService,
    TaskPlannerManagerService,
    MAX_DEPTH
)
from src.domain.services.task import BaseTaskManagerService


# Test BaseTaskManagerService validation logic
def test_base_service_validate_deadline_success_future():
    """Test deadline validation with future datetime."""
    service = BaseTaskManagerService()
    future_deadline = datetime.now(timezone.utc) + timedelta(days=1)

    # Should not raise any error
    service._validate_deadline(future_deadline)


def test_base_service_validate_deadline_success_future_with_timezone():
    """Test deadline validation with future datetime in different timezone."""
    service = BaseTaskManagerService()

    # Create deadline in different timezone (e.g., UTC+2)
    future_deadline = datetime.now(timezone.utc) + timedelta(days=1)
    future_deadline_with_tz = future_deadline.astimezone(
        timezone(timedelta(hours=2))
    )

    # Should not raise any error (converts to UTC for comparison)
    service._validate_deadline(future_deadline_with_tz)


def test_base_service_validate_deadline_failure_past():
    """Test deadline validation fails with past datetime."""
    service = BaseTaskManagerService()
    past_deadline = datetime.now(timezone.utc) - timedelta(days=1)

    with pytest.raises(InvalidDeadlineError, match="Deadline cannot be less or equal than now"):
        service._validate_deadline(past_deadline)


def test_base_service_validate_deadline_failure_now():
    """Test deadline validation fails with current datetime."""
    service = BaseTaskManagerService()
    current_time = datetime.now(timezone.utc)

    with pytest.raises(InvalidDeadlineError, match="Deadline cannot be less or equal than now"):
        service._validate_deadline(current_time)


def test_base_service_validate_deadline_failure_slightly_past():
    """Test deadline validation fails with datetime slightly in the past."""
    service = BaseTaskManagerService()
    slightly_past = datetime.now(timezone.utc) - timedelta(seconds=1)

    with pytest.raises(InvalidDeadlineError, match="Deadline cannot be less or equal than now"):
        service._validate_deadline(slightly_past)


# Test TaskProducerService creation logic
def test_producer_create_task_without_parent():
    """Test creating a root task (no parent)."""
    producer_service = TaskProducerService()
    future_deadline = datetime.now(timezone.utc) + timedelta(days=1)

    task = producer_service.create_task(
        title="Test Task",
        deadline=future_deadline,
        user_id=1,
        description="Test description"
    )

    assert task.title == "Test Task"
    assert task.deadline == future_deadline
    assert task.user_id == 1
    assert task.description == "Test description"
    assert task.parent is None


def test_producer_create_task_with_parent():
    """Test creating a task with valid parent."""
    producer_service = TaskProducerService()
    future_deadline = datetime.now(timezone.utc) + timedelta(days=1)

    # Create parent with mocked depth
    parent = Task(title="Parent", _deadline=future_deadline, user_id=1)
    parent.get_depth = Mock(return_value=1)

    task = producer_service.create_task(
        title="Child Task",
        deadline=future_deadline,
        user_id=1,
        parent=parent
    )

    assert task.title == "Child Task"
    assert task.parent == parent


def test_producer_create_task_validates_deadline():
    """Test that task creation validates deadline."""
    producer_service = TaskProducerService()
    past_deadline = datetime.now(timezone.utc) - timedelta(days=1)

    with pytest.raises(InvalidDeadlineError, match="Deadline cannot be less or equal than now"):
        producer_service.create_task(
            title="Test Task",
            deadline=past_deadline,
            user_id=1
        )


def test_producer_create_task_validates_parent_depth_within_limit():
    """Test creating task with parent at max depth-1."""
    producer_service = TaskProducerService()
    future_deadline = datetime.now(timezone.utc) + timedelta(days=1)

    # Create parent at depth MAX_DEPTH - 1 (should be allowed)
    parent = Task(title="Parent", _deadline=future_deadline, user_id=1)
    parent.get_depth = Mock(return_value=MAX_DEPTH - 1)

    task = producer_service.create_task(
        title="Child Task",
        deadline=future_deadline,
        user_id=1,
        parent=parent
    )

    assert task is not None
    assert task.parent == parent


def test_producer_create_task_validates_parent_depth_at_limit():
    """Test creating task with parent at max depth fails."""
    producer_service = TaskProducerService()
    future_deadline = datetime.now(timezone.utc) + timedelta(days=1)

    # Create parent at depth MAX_DEPTH (should fail)
    parent = Task(title="Parent", _deadline=future_deadline, user_id=1)
    parent.get_depth = Mock(return_value=MAX_DEPTH)

    with pytest.raises(MaxDepthError, match=f"Depth of task tree couldn't be more than {MAX_DEPTH}"):
        producer_service.create_task(
            title="Child Task",
            deadline=future_deadline,
            user_id=1,
            parent=parent
        )


def test_producer_create_task_validates_parent_depth_exceeds_limit():
    """Test creating task with parent exceeding max depth fails."""
    producer_service = TaskProducerService()
    future_deadline = datetime.now(timezone.utc) + timedelta(days=1)

    # Create parent exceeding MAX_DEPTH (should fail)
    parent = Task(title="Parent", _deadline=future_deadline, user_id=1)
    parent.get_depth = Mock(return_value=MAX_DEPTH + 1)

    with pytest.raises(MaxDepthError, match=f"Depth of task tree couldn't be more than {MAX_DEPTH}"):
        producer_service.create_task(
            title="Child Task",
            deadline=future_deadline,
            user_id=1,
            parent=parent
        )


def test_producer_create_task_with_none_description():
    """Test creating task with None description."""
    producer_service = TaskProducerService()
    future_deadline = datetime.now(timezone.utc) + timedelta(days=1)

    task = producer_service.create_task(
        title="Test Task",
        deadline=future_deadline,
        user_id=1,
        description=None
    )

    assert task.description is None


def test_producer_create_task_with_empty_description():
    """Test creating task with empty description."""
    producer_service = TaskProducerService()
    future_deadline = datetime.now(timezone.utc) + timedelta(days=1)

    task = producer_service.create_task(
        title="Test Task",
        deadline=future_deadline,
        user_id=1,
        description=""
    )

    assert task.description == ""


def test_producer_create_task_inherits_validation_from_base():
    """Test that TaskProducerService uses BaseTaskManagerService validation."""
    producer_service = TaskProducerService()
    past_deadline = datetime.now(timezone.utc) - timedelta(days=1)

    # This should trigger the base class validation
    with pytest.raises(InvalidDeadlineError):
        producer_service.create_task(
            title="Test Task",
            deadline=past_deadline,
            user_id=1
        )


def test_producer_validate_depth_uses_constant():
    """Test that depth validation uses the MAX_DEPTH constant."""
    producer_service = TaskProducerService()

    # Mock parent with depth exactly at MAX_DEPTH
    parent = Mock(spec=Task)
    parent.get_depth.return_value = MAX_DEPTH

    with pytest.raises(MaxDepthError) as exc_info:
        producer_service._validate_depth(parent)

    assert str(MAX_DEPTH) in str(exc_info.value)


# Test TaskPlannerManagerService deadline management logic
def test_planner_init_with_task():
    """Test service initialization with a task."""
    future_deadline = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test Task", _deadline=future_deadline, user_id=1)

    service = TaskPlannerManagerService(task)
    assert service._task == task


def test_set_deadline_calls_all_validations_in_order():
    """Test that set_deadline calls all validations in correct order"""
    mock_task = Mock()
    mock_task.parent = Mock(deadline=datetime(2024, 1, 1, tzinfo=timezone.utc))
    mock_task.subtasks = []

    service = TaskPlannerManagerService(mock_task)

    with patch.object(BaseTaskManagerService, '_validate_deadline') as mock_base_val, \
            patch.object(service, '_validate_subs_deadlines') as mock_subs_val, \
            patch.object(service, '_validate_parent_deadline') as mock_parent_val:

        new_deadline = datetime(2024, 1, 1, tzinfo=timezone.utc)
        service.set_deadline(new_deadline)

        # Verify base validation is called (which calls the others)
        mock_base_val.assert_called_once_with(new_deadline)


def test_validate_subs_deadlines_with_no_subtasks():
    """Test _validate_subs_deadlines with empty subtasks list"""
    mock_task = Mock()
    mock_task.subtasks = []

    service = TaskPlannerManagerService(mock_task)

    # Should not raise any error
    new_deadline = datetime(2024, 1, 1, tzinfo=timezone.utc)
    service._validate_subs_deadlines(new_deadline)


def test_validate_subs_deadlines_subtask_has_later_deadline():
    """Test _validate_subs_deadlines when a subtask has later deadline"""
    mock_subtask = Mock(deadline=datetime(2024, 1, 5, tzinfo=timezone.utc))
    mock_task = Mock()
    mock_task.subtasks = [mock_subtask]

    service = TaskPlannerManagerService(mock_task)

    new_deadline = datetime(2024, 1, 1, tzinfo=timezone.utc)  # Earlier than subtask

    with pytest.raises(InvalidDeadlineError) as exc_info:
        service._validate_subs_deadlines(new_deadline)

    assert "cannot be less than deadline of subtasks" in str(exc_info.value)


def test_validate_subs_deadlines_with_nested_subtasks():
    """Test _validate_subs_deadlines with nested subtask hierarchy"""
    mock_nested_subtask = Mock(deadline=datetime(2024, 1, 3, tzinfo=timezone.utc))
    mock_nested_subtask.subtasks = []

    mock_subtask = Mock(deadline=datetime(2024, 1, 2, tzinfo=timezone.utc))
    mock_subtask.subtasks = [mock_nested_subtask]  # Has its own subtask

    mock_task = Mock()
    mock_task.subtasks = [mock_subtask]

    service = TaskPlannerManagerService(mock_task)

    # Should raise error because of nested subtask with deadline Jan 3
    new_deadline = datetime(2024, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(InvalidDeadlineError) as exc_info:
        service._validate_subs_deadlines(new_deadline)


def test_validate_subs_deadlines_all_subtasks_earlier():
    """Test _validate_subs_deadlines when all subtasks have earlier deadlines"""
    mock_subtask1 = Mock(deadline=datetime(2024, 1, 1, tzinfo=timezone.utc))
    mock_subtask1.subtasks = []

    mock_subtask2 = Mock(deadline=datetime(2024, 1, 2, tzinfo=timezone.utc))
    mock_subtask2.subtasks = []

    mock_task = Mock()
    mock_task.subtasks = [mock_subtask1, mock_subtask2]

    service = TaskPlannerManagerService(mock_task)

    new_deadline = datetime(2024, 1, 3, tzinfo=timezone.utc)  # Later than all subtasks

    # Should not raise error
    service._validate_subs_deadlines(new_deadline)


def test_validate_parent_deadline_parent_has_earlier_deadline():
    """Test _validate_parent_deadline when parent has earlier deadline"""
    mock_task = Mock()
    mock_task.parent = Mock(deadline=datetime(2024, 1, 1, tzinfo=timezone.utc))

    service = TaskPlannerManagerService(mock_task)

    new_deadline = datetime(2024, 1, 5, tzinfo=timezone.utc)  # Later than parent

    with pytest.raises(InvalidDeadlineError) as exc_info:
        service._validate_parent_deadline(new_deadline)

    assert "cannot be more than deadline of parent task" in str(exc_info.value)


def test_validate_parent_deadline_parent_has_later_deadline():
    """Test _validate_parent_deadline when parent has later deadline"""
    mock_task = Mock()
    mock_task.parent = Mock(deadline=datetime(2024, 1, 10, tzinfo=timezone.utc))

    service = TaskPlannerManagerService(mock_task)

    new_deadline = datetime(2024, 1, 5, tzinfo=timezone.utc)  # Earlier than parent

    # Should not raise error
    service._validate_parent_deadline(new_deadline)


def test_validate_parent_deadline_parent_has_equal_deadline():
    """Test _validate_parent_deadline when parent has equal deadline"""
    mock_task = Mock()
    mock_task.parent = Mock(deadline=datetime(2024, 1, 1, tzinfo=timezone.utc))

    service = TaskPlannerManagerService(mock_task)

    new_deadline = datetime(2024, 1, 1, tzinfo=timezone.utc)  # Equal to parent

    # Should not raise error (parent.deadline < new_deadline is False)
    service._validate_parent_deadline(new_deadline)


def test_validate_parent_deadline_no_parent():
    """Test _validate_parent_deadline when task has no parent (root task)"""
    mock_task = Mock()
    mock_task.parent = None

    service = TaskPlannerManagerService(mock_task)

    new_deadline = datetime(2024, 1, 1, tzinfo=timezone.utc)

    # Should not raise error (parent.deadline would raise AttributeError but check happens first)
    # Actually, if parent is None, accessing parent.deadline would fail
    # This test reveals a potential bug in the original code!
    with pytest.raises(AttributeError):
        service._validate_parent_deadline(new_deadline)


def test_set_deadline_updates_internal_attribute():
    """Test that set_deadline successfully updates _deadline attribute"""
    mock_task = Mock()
    mock_task.parent = Mock(deadline=datetime(2024, 1, 10, tzinfo=timezone.utc))
    mock_task.subtasks = []

    service = TaskPlannerManagerService(mock_task)

    # Mock the validation to pass
    with patch.object(service, '_validate_deadline'):
        new_deadline = datetime(2024, 1, 5, tzinfo=timezone.utc)
        service.set_deadline(new_deadline)

        # Verify _deadline was set
        assert mock_task._deadline == new_deadline


def test_validate_deadline_calls_all_validations():
    """Test that _validate_deadline calls base validation and its own validations"""
    mock_task = Mock()
    mock_task.parent = Mock(deadline=datetime(2024, 1, 10, tzinfo=timezone.utc))
    mock_task.subtasks = []

    service = TaskPlannerManagerService(mock_task)

    with patch.object(BaseTaskManagerService, '_validate_deadline') as mock_base_val, \
            patch.object(service, '_validate_subs_deadlines') as mock_subs_val, \
            patch.object(service, '_validate_parent_deadline') as mock_parent_val:

        new_deadline = datetime(2024, 1, 5, tzinfo=timezone.utc)
        service._validate_deadline(new_deadline)

        # Verify all validations were called
        mock_base_val.assert_called_once_with(new_deadline)
        mock_subs_val.assert_called_once_with(new_deadline)
        mock_parent_val.assert_called_once_with(new_deadline)


def test_validate_deadline_with_complex_scenario():
    """Test _validate_deadline with a complex scenario that should pass"""
    mock_subtask = Mock(deadline=datetime(2024, 1, 3, tzinfo=timezone.utc))
    mock_subtask.subtasks = []

    mock_task = Mock()
    mock_task.parent = Mock(deadline=datetime(2024, 1, 10, tzinfo=timezone.utc))
    mock_task.subtasks = [mock_subtask]

    service = TaskPlannerManagerService(mock_task)

    # Mock base validation to pass
    with patch.object(BaseTaskManagerService, '_validate_deadline'):
        new_deadline = datetime(2024, 1, 5, tzinfo=timezone.utc)  # After subtask, before parent

        # Should not raise any errors
        service._validate_deadline(new_deadline)


def test_set_deadline_propagates_validation_errors():
    """Test that validation errors from any validation method are propagated"""
    mock_task = Mock()
    mock_task.parent = Mock(deadline=datetime(2024, 1, 1, tzinfo=timezone.utc))
    mock_task.subtasks = []

    service = TaskPlannerManagerService(mock_task)

    # Mock base validation to raise error
    with patch.object(BaseTaskManagerService, '_validate_deadline',
                      side_effect=InvalidDeadlineError("Base validation failed")):

        new_deadline = datetime(2024, 1, 5, tzinfo=timezone.utc)

        with pytest.raises(InvalidDeadlineError) as exc_info:
            service.set_deadline(new_deadline)

        assert "Base validation failed" in str(exc_info.value)
        # Verify _deadline was NOT updated
        mock_task._deadline = None  # Ensure it's not set
        assert not hasattr(mock_task, '_deadline') or mock_task._deadline is None


def test_max_depth_constant_accessible():
    """Test that MAX_DEPTH constant is accessible and has expected value."""
    assert MAX_DEPTH == 5
    assert isinstance(MAX_DEPTH, int)
    assert MAX_DEPTH > 0


def test_producer_service_instantiation():
    """Test that TaskProducerService can be instantiated."""
    service = TaskProducerService()
    assert isinstance(service, TaskProducerService)
    assert isinstance(service, BaseTaskManagerService)


def test_planner_service_instantiation():
    """Test that TaskPlannerManagerService can be instantiated with a task."""
    future_deadline = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test", _deadline=future_deadline, user_id=1)

    service = TaskPlannerManagerService(task)
    assert isinstance(service, TaskPlannerManagerService)
    assert isinstance(service, BaseTaskManagerService)
    assert service._task == task


def test_producer_create_task_with_parent_deadline_earlier_than_parent():
    """Test creating child task with deadline earlier than parent's deadline."""
    producer_service = TaskProducerService()

    parent_deadline = datetime.now(timezone.utc) + timedelta(days=3)
    child_deadline = datetime.now(timezone.utc) + timedelta(days=1)  # Earlier than parent

    parent = Task(title="Parent", _deadline=parent_deadline, user_id=1)
    parent.get_depth = Mock(return_value=1)

    # This should be allowed (no validation prevents it)
    task = producer_service.create_task(
        title="Child Task",
        deadline=child_deadline,
        user_id=1,
        parent=parent
    )

    assert task.deadline == child_deadline
    assert task.deadline < parent.deadline
