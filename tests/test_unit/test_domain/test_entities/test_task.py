import pytest

from datetime import datetime, timedelta, timezone

from src.domain.entities import Task
from src.domain.entities.exceptions import UnfinishedTaskError, HasNoDirectAccessError


pytest_mark_asyncio = pytest.mark.asyncio


def test_task_creation():
    """Test basic task creation."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test Task", _deadline=deadline, user_id=1, description="")

    assert task.title == "Test Task"
    assert task.deadline == deadline
    assert task.user_id == 1
    assert task.id is None  # Not set initially
    assert task.description == ''
    assert task.parent is None
    assert task.parent_id is None
    assert task.subtasks == []
    assert not task.is_done
    assert task.pass_date is None


def test_task_with_description():
    """Test task creation with description."""
    deadline = datetime.now(timezone.utc) + timedelta(days=2)
    task = Task(
        title="Test Task",
        _deadline=deadline,
        user_id=1,
        description="Test description"
    )

    assert task.description == "Test description"


def test_task_creation_date_auto_set():
    """Test that creation_date is automatically set to UTC."""
    before_creation = datetime.now(timezone.utc)
    task = Task(
        title="Test Task",
        _deadline=datetime.now(timezone.utc) + timedelta(days=1),
        user_id=1,
        description=""
    )
    after_creation = datetime.now(timezone.utc)

    # Check creation_date is set and is timezone-aware UTC
    assert task.creation_date is not None
    assert task.creation_date.tzinfo == timezone.utc
    assert before_creation <= task.creation_date <= after_creation


def test_task_with_parent():
    """Test task with parent relationship."""
    parent_deadline = datetime.now(timezone.utc) + timedelta(days=3)
    child_deadline = datetime.now(timezone.utc) + timedelta(days=2)

    parent = Task(title="Parent", _deadline=parent_deadline, user_id=1, description="")
    child = Task(title="Child", _deadline=child_deadline, user_id=1, parent=parent, description="")
    parent.subtasks.append(child)

    assert child.parent == parent
    assert parent is child.parent  # Should be the same object
    assert child in parent.subtasks


def test_is_root_property():
    """Test is_root property."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)

    # Root task (no parent)
    root_task = Task(title="Root", _deadline=deadline, user_id=1, description="")
    assert root_task.is_root is True

    # Child task
    parent = Task(title="Parent", _deadline=deadline, user_id=1, description="")
    child = Task(title="Child", _deadline=deadline, user_id=1, parent=parent, description="")
    child.parent_id = 1
    parent.subtasks.append(child)
    assert child.is_root is False


def test_is_done_property():
    """Test is_done property."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test", _deadline=deadline, user_id=1, description="")

    # Initially not done
    assert not task.is_done
    assert task.pass_date is None

    # Mark as done
    task.force_mark_as_done()
    assert task.is_done
    assert task.pass_date is not None
    assert task.pass_date.tzinfo == timezone.utc


def test_deadline_protected_setter():
    """Test that deadline cannot be set directly."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test", _deadline=deadline, user_id=1, description="")

    # Should be able to get deadline
    assert task.deadline == deadline

    # Should not be able to set deadline directly
    with pytest.raises(HasNoDirectAccessError, match="Cannot set deadline directly"):
        task.deadline = datetime.now(timezone.utc)


def test_pass_date_protected_setter():
    """Test that pass_date cannot be set directly."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test", _deadline=deadline, user_id=1, description="")

    # Initially None
    assert task.pass_date is None

    # Should not be able to set pass_date directly
    with pytest.raises(HasNoDirectAccessError, match="Cannot set pass date directly"):
        task.pass_date = datetime.now(timezone.utc)


def test_force_mark_as_done():
    """Test force_mark_as_done method."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)

    # Create task hierarchy
    parent = Task(title="Parent", _deadline=deadline, user_id=1, description="")
    child1 = Task(title="Child1", _deadline=deadline, user_id=1, parent=parent, description="")
    child2 = Task(title="Child2", _deadline=deadline, user_id=1, parent=parent, description="")
    parent.subtasks.append(child1)
    parent.subtasks.append(child2)
    grandchild = Task(title="Grandchild", _deadline=deadline, user_id=1, parent=child1, description="")
    child1.subtasks.append(grandchild)

    # Initially none are done
    assert not parent.is_done
    assert not child1.is_done
    assert not child2.is_done
    assert not grandchild.is_done

    # Force mark parent as done - should mark all descendants
    before_mark = datetime.now(timezone.utc)
    parent.force_mark_as_done()
    after_mark = datetime.now(timezone.utc)

    # Check all tasks are marked as done
    assert parent.is_done
    assert child1.is_done
    assert child2.is_done
    assert grandchild.is_done

    # Check pass_date is set and is recent
    assert parent.pass_date is not None
    assert before_mark <= parent.pass_date <= after_mark
    assert parent.pass_date.tzinfo == timezone.utc


def test_mark_as_done_success():
    """Test successful mark_as_done when all subtasks are done."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)

    # Create task hierarchy
    parent = Task(title="Parent", _deadline=deadline, user_id=1, description="")
    child1 = Task(title="Child1", _deadline=deadline, user_id=1, parent=parent, description="")
    child2 = Task(title="Child2", _deadline=deadline, user_id=1, parent=parent, description="")

    # Mark all children as done first
    child1.force_mark_as_done()
    child2.force_mark_as_done()

    # Now parent can be marked as done
    before_mark = datetime.now(timezone.utc)
    parent.mark_as_done()
    after_mark = datetime.now(timezone.utc)

    assert parent.is_done
    assert parent.pass_date is not None
    assert before_mark <= parent.pass_date <= after_mark


def test_mark_as_done_failure_unfinished_subtasks():
    """Test mark_as_done fails when subtasks are not finished."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)

    # Create task hierarchy
    parent = Task(title="Parent", _deadline=deadline, user_id=1, description="")
    child1 = Task(title="Child1", _deadline=deadline, user_id=1, parent=parent, description="")
    child2 = Task(title="Child2", _deadline=deadline, user_id=1, parent=parent, description="")
    parent.subtasks.append(child1)
    parent.subtasks.append(child2)

    # Mark only one child as done
    child1.force_mark_as_done()
    # child2 is not done

    # Parent should not be able to mark as done
    with pytest.raises(UnfinishedTaskError, match="Unable finish task while subtasks not fininshed"):
        parent.mark_as_done()

    assert not parent.is_done
    assert parent.pass_date is None


def test_mark_as_done_nested_hierarchy():
    """Test mark_as_done with nested hierarchy."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)

    # Create deep hierarchy
    root = Task(title="Root", _deadline=deadline, user_id=1, description="")
    level1 = Task(title="Level1", _deadline=deadline, user_id=1, parent=root, description="")
    level2 = Task(title="Level2", _deadline=deadline, user_id=1, parent=level1, description="")
    level3 = Task(title="Level3", _deadline=deadline, user_id=1, parent=level2, description="")

    # Mark from bottom up
    level3.force_mark_as_done()
    level2.force_mark_as_done()
    level1.force_mark_as_done()

    # Now root can be marked as done
    root.mark_as_done()
    assert root.is_done


def test_get_depth():
    """Test get_depth method for hierarchy depth calculation."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)

    # Root task
    root = Task(title="Root", _deadline=deadline, user_id=1, description="")
    assert root.get_depth() == 1

    # First level child
    child1 = Task(title="Child1", _deadline=deadline, user_id=1, parent=root, description="")
    assert child1.get_depth() == 2

    # Second level child
    grandchild = Task(title="Grandchild", _deadline=deadline, user_id=1, parent=child1, description="")
    assert grandchild.get_depth() == 3

    # Third level child
    great_grandchild = Task(title="GreatGrandchild", _deadline=deadline,
                            user_id=1, parent=grandchild, description="")
    assert great_grandchild.get_depth() == 4


def test_get_depth_with_multiple_branches():
    """Test get_depth with multiple branches."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)

    root = Task(title="Root", _deadline=deadline, user_id=1, description="")
    branch1 = Task(title="Branch1", _deadline=deadline, user_id=1, parent=root, description="")
    branch2 = Task(title="Branch2", _deadline=deadline, user_id=1, parent=root, description="")
    leaf1 = Task(title="Leaf1", _deadline=deadline, user_id=1, parent=branch1, description="")
    leaf2 = Task(title="Leaf2", _deadline=deadline, user_id=1, parent=branch2, description="")

    assert root.get_depth() == 1
    assert branch1.get_depth() == 2
    assert branch2.get_depth() == 2
    assert leaf1.get_depth() == 3
    assert leaf2.get_depth() == 3


def test_task_equality_by_identity():
    """Test that tasks are compared by identity, not value."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)

    task1 = Task(title="Task1", _deadline=deadline, user_id=1, description="")
    task2 = Task(title="Task2", _deadline=deadline, user_id=1, description="")
    task3 = task1  # Same reference

    assert task1 is not task2  # Different objects
    assert task1 is task3      # Same object
    assert task1 == task1      # Identity equality
    assert task1 != task2      # Different identities


def test_subtasks_list_manipulation():
    """Test manipulating subtasks list."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)

    parent = Task(title="Parent", _deadline=deadline, user_id=1, description="")
    child1 = Task(title="Child1", _deadline=deadline, user_id=1, parent=parent, description="")
    child2 = Task(title="Child2", _deadline=deadline, user_id=1, parent=parent, description="")
    parent.subtasks.append(child1)
    parent.subtasks.append(child2)

    # Check subtasks were added
    assert len(parent.subtasks) == 2
    assert child1 in parent.subtasks
    assert child2 in parent.subtasks

    # Manually manipulate subtasks list (if needed for tests)
    parent.subtasks.append(Task(title="Child3", _deadline=deadline, user_id=1, description=""))
    assert len(parent.subtasks) == 3


def test_task_repr():
    """Test task string representation."""
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test Task", _deadline=deadline, user_id=1, description="Test")

    # Basic repr test
    repr_str = repr(task)
    assert "Task" in repr_str
    assert "Test Task" in repr_str
    # Don't test exact format as dataclass repr may vary


# Fixtures for common test data
@pytest.fixture
def sample_deadline():
    return datetime.now(timezone.utc) + timedelta(days=1)


@pytest.fixture
def root_task(sample_deadline):
    return Task(title="Root", _deadline=sample_deadline, user_id=1)


@pytest.fixture
def task_hierarchy(sample_deadline):
    """Create a 3-level task hierarchy with proper bidirectional relationships."""
    root = Task(title="Root", _deadline=sample_deadline, user_id=1, description="")
    child1 = Task(title="Child1", _deadline=sample_deadline, user_id=1, parent=root, description="")
    child2 = Task(title="Child2", _deadline=sample_deadline, user_id=1, parent=root, description="")
    grandchild = Task(title="Grandchild", _deadline=sample_deadline, user_id=1, parent=child1, description="")

    # Manually set up bidirectional relationships for unit tests
    root.subtasks = [child1, child2]
    child1.subtasks = [grandchild]

    return root, child1, child2, grandchild

# Tests using fixtures


def test_hierarchy_with_fixture(task_hierarchy):
    """Test hierarchy using fixture."""
    root, child1, child2, grandchild = task_hierarchy

    assert root.parent is None
    assert child1.parent == root
    assert child2.parent == root
    assert grandchild.parent == child1

    assert len(root.subtasks) == 2
    assert len(child1.subtasks) == 1
    assert len(child2.subtasks) == 0


def test_mark_done_hierarchy_with_fixture(task_hierarchy):
    """Test mark_as_done with fixture hierarchy."""
    root, child1, child2, grandchild = task_hierarchy

    # Mark all tasks as done from bottom up
    grandchild.force_mark_as_done()
    child1.force_mark_as_done()
    child2.force_mark_as_done()

    # Root can now be marked as done
    root.mark_as_done()
    assert root.is_done
    assert all(task.is_done for task in [child1, child2, grandchild])
