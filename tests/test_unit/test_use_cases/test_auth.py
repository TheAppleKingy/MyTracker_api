import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.application.use_cases.auth import *
from src.domain.entities import User
from src.application.use_cases.exceptions import UserExistsError, UndefinedUserError, HasNoAccessError, UndefinedTaskError
from src.application.dto.users import RegisterUserDTO


def test_execute_successful_registration():
    """Test successful user registration flow"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()

    async def aenter(self):
        return mock_uow

    async def aexit(self, *args):
        return False
    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    # Setup mocks
    mock_user_repo.count_by_tg_name.return_value = 0

    register_use_case = RegisterUser(mock_uow, mock_user_repo)
    dto = RegisterUserDTO(tg_name="test_user")

    # Act
    result = asyncio.run(register_use_case.execute(dto))

    # Assert
    # Verify user repo was called with correct tg_name
    mock_user_repo.count_by_tg_name.assert_called_once_with("test_user")

    # Verify uow.save() was called
    mock_uow.save.assert_called_once()

    # Verify result is None (since nothing is returned)
    assert result is None


def test_execute_user_already_exists():
    """Test registration fails when user already exists"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()

    # User already exists
    mock_user_repo.count_by_tg_name.return_value = 1

    register_use_case = RegisterUser(mock_uow, mock_user_repo)
    dto = RegisterUserDTO(tg_name="existing_user")

    # Act & Assert
    with pytest.raises(UserExistsError) as exc_info:
        asyncio.run(register_use_case.execute(dto))

    assert "User with this telegram name already exists" in str(exc_info.value)

    # Verify count was called
    mock_user_repo.count_by_tg_name.assert_called_once_with("existing_user")

    # Verify uow.save() was NOT called
    mock_uow.save.assert_not_called()


def test_execute_context_manager_entered():
    """Test that uow is used as async context manager"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()

    mock_user_repo.count_by_tg_name.return_value = 0

    register_use_case = RegisterUser(mock_uow, mock_user_repo)
    dto = RegisterUserDTO(tg_name="test_user")

    # Act
    asyncio.run(register_use_case.execute(dto))

    # Assert
    # Verify uow.__aenter__ was called (entering context manager)
    mock_uow.__aenter__.assert_called_once()

    # Verify uow.__aexit__ was called (exiting context manager)
    mock_uow.__aexit__.assert_called_once()


def test_execute_save_called_with_user_object():
    """Test that save() is called with a User object"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()

    async def aenter(self):
        return mock_uow

    async def aexit(self, *args):
        return False
    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    mock_user_repo.count_by_tg_name.return_value = 0

    register_use_case = RegisterUser(mock_uow, mock_user_repo)
    dto = RegisterUserDTO(tg_name="test_user")

    # Act
    asyncio.run(register_use_case.execute(dto))

    # Assert
    # Verify save was called
    mock_uow.save.assert_called_once()

    # Verify save was called with a User instance
    saved_arg = mock_uow.save.call_args[0][0]
    assert isinstance(saved_arg, User)
    assert saved_arg.tg_name == "test_user"


def test_execute_uow_context_returns_itself():
    """Test that uow context returns itself for save()"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()

    # Important: uow.__aenter__ should return the same uow object
    mock_uow.__aenter__.return_value = mock_uow
    mock_user_repo.count_by_tg_name.return_value = 0

    register_use_case = RegisterUser(mock_uow, mock_user_repo)
    dto = RegisterUserDTO(tg_name="test_user")

    # Act
    asyncio.run(register_use_case.execute(dto))

    # Assert
    # Verify save was called on the uow instance
    mock_uow.save.assert_called_once()


def test_execute_different_tg_names():
    """Test with different telegram names"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()

    # Different counts for different names
    def count_side_effect(tg_name):
        return 1 if tg_name == "existing" else 0

    mock_user_repo.count_by_tg_name.side_effect = count_side_effect

    async def aenter(self):
        return mock_uow

    async def aexit(self, *args):
        return False
    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    register_use_case = RegisterUser(mock_uow, mock_user_repo)

    # Test 1: New user
    dto1 = RegisterUserDTO(tg_name="new_user")
    asyncio.run(register_use_case.execute(dto1))
    mock_user_repo.count_by_tg_name.assert_called_with("new_user")
    mock_uow.save.assert_called_once()

    # Reset mocks for second test
    mock_user_repo.count_by_tg_name.reset_mock()
    mock_uow.save.reset_mock()

    # Test 2: Existing user (should fail)
    dto2 = RegisterUserDTO(tg_name="existing")
    with pytest.raises(UserExistsError):
        asyncio.run(register_use_case.execute(dto2))

    mock_user_repo.count_by_tg_name.assert_called_with("existing")
    mock_uow.save.assert_not_called()


def test_execute_count_returns_non_zero():
    """Test with count returning non-zero values"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()

    # Test with different non-zero counts
    for count in [1, 5, 100]:
        mock_user_repo.count_by_tg_name.return_value = count

        register_use_case = RegisterUser(mock_uow, mock_user_repo)
        dto = RegisterUserDTO(tg_name="user")

        with pytest.raises(UserExistsError):
            asyncio.run(register_use_case.execute(dto))

        # Reset mock for next iteration
        mock_user_repo.count_by_tg_name.reset_mock()
        mock_uow.save.reset_mock()


def test_execute_empty_tg_name():
    """Test registration with empty telegram name (if allowed by DTO)"""
    # Arrange
    # Create a Mock instead of AsyncMock since save() is synchronous
    mock_uow = Mock()
    mock_user_repo = AsyncMock()

    mock_user_repo.count_by_tg_name.return_value = 0

    # Add async context manager methods
    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return True

    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit

    register_use_case = RegisterUser(mock_uow, mock_user_repo)
    dto = RegisterUserDTO(tg_name="")  # Empty name

    # Act
    result = asyncio.run(register_use_case.execute(dto))

    # Assert
    mock_user_repo.count_by_tg_name.assert_called_once_with("")
    mock_uow.save.assert_called_once()
    assert result is None


def test_execute_uow_save_raises_exception():
    """Test behavior when uow.save() raises an exception"""
    # Arrange
    # Create a Mock (not AsyncMock) with specific async methods
    mock_uow = Mock()
    mock_user_repo = AsyncMock()
    mock_user_repo.count_by_tg_name.return_value = 0
    # Configure async context manager methods

    async def aenter(self):
        return mock_uow

    async def aexit(self, exc_type, exc_val, exc_tb):
        return False  # Don't suppress exceptions
    mock_uow.__aenter__ = aenter
    mock_uow.__aexit__ = aexit
    # Now save is a regular Mock method, so side_effect works
    mock_uow.save.side_effect = Exception("Database error")
    register_use_case = RegisterUser(mock_uow, mock_user_repo)
    dto = RegisterUserDTO(tg_name="test_user")
    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        asyncio.run(register_use_case.execute(dto))
    print(exc_info.value)
    assert "Database error" in str(exc_info.value)


def test_execute_repository_raises_exception():
    """Test behavior when repository raises an exception"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()

    mock_user_repo.count_by_tg_name.side_effect = Exception("DB connection error")

    register_use_case = RegisterUser(mock_uow, mock_user_repo)
    dto = RegisterUserDTO(tg_name="test_user")

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        asyncio.run(register_use_case.execute(dto))

    assert "DB connection error" in str(exc_info.value)

    # Verify save was NOT called
    mock_uow.save.assert_not_called()

# ================= test auth use case ==========================#


def test_execute_successful_authentication():
    """Test successful authentication with valid token"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_auth_service = Mock()  # Not async

    # Setup mocks
    valid_token = "valid_token_123"
    tg_name = "test_user"
    user_id = 42

    mock_auth_service.get_tg_name_from_token.return_value = tg_name
    mock_user_repo.get_by_tg_name.return_value = Mock(id=user_id)

    authenticate_use_case = AuthenticateUser(mock_uow, mock_user_repo, mock_auth_service)

    # Act
    result = asyncio.run(authenticate_use_case.execute(valid_token))

    # Assert
    mock_auth_service.get_tg_name_from_token.assert_called_once_with(valid_token)
    mock_user_repo.get_by_tg_name.assert_called_once_with(tg_name)

    assert result == user_id


def test_execute_no_token_raises_error():
    """Test authentication with no token raises UndefinedUserError"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_auth_service = Mock()

    authenticate_use_case = AuthenticateUser(mock_uow, mock_user_repo, mock_auth_service)

    # Act & Assert
    with pytest.raises(UndefinedUserError) as exc_info:
        asyncio.run(authenticate_use_case.execute(None))

    assert "Unauthorized" in str(exc_info.value)
    assert exc_info.value.status == 401

    # Verify no other calls were made
    mock_auth_service.get_tg_name_from_token.assert_not_called()
    mock_user_repo.get_by_tg_name.assert_not_called()


def test_execute_empty_token_raises_error():
    """Test authentication with empty token raises UndefinedUserError"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_auth_service = Mock()

    authenticate_use_case = AuthenticateUser(mock_uow, mock_user_repo, mock_auth_service)

    # Act & Assert
    with pytest.raises(UndefinedUserError) as exc_info:
        asyncio.run(authenticate_use_case.execute(""))

    assert "Unauthorized" in str(exc_info.value)
    assert exc_info.value.status == 401

    # Verify auth service was called but returned empty
    mock_auth_service.get_tg_name_from_token.assert_not_called()
    mock_user_repo.get_by_tg_name.assert_not_called()


def test_execute_invalid_token_raises_error():
    """Test authentication with invalid token raises UndefinedUserError"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_auth_service = Mock()

    invalid_token = "invalid_token"
    mock_auth_service.get_tg_name_from_token.return_value = None

    authenticate_use_case = AuthenticateUser(mock_uow, mock_user_repo, mock_auth_service)

    # Act & Assert
    with pytest.raises(UndefinedUserError) as exc_info:
        asyncio.run(authenticate_use_case.execute(invalid_token))

    assert "Unauthorized" in str(exc_info.value)
    assert exc_info.value.status == 401

    mock_auth_service.get_tg_name_from_token.assert_called_once_with(invalid_token)
    mock_user_repo.get_by_tg_name.assert_not_called()


def test_execute_user_not_found_raises_error():
    """Test authentication when user doesn't exist in database"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_auth_service = Mock()

    valid_token = "valid_token"
    tg_name = "non_existent_user"

    mock_auth_service.get_tg_name_from_token.return_value = tg_name
    mock_user_repo.get_by_tg_name.return_value = None

    authenticate_use_case = AuthenticateUser(mock_uow, mock_user_repo, mock_auth_service)

    # Act & Assert
    with pytest.raises(UndefinedUserError) as exc_info:
        asyncio.run(authenticate_use_case.execute(valid_token))

    assert "Unauthorized" in str(exc_info.value)
    assert exc_info.value.status == 401

    mock_auth_service.get_tg_name_from_token.assert_called_once_with(valid_token)
    mock_user_repo.get_by_tg_name.assert_called_once_with(tg_name)


def test_execute_uow_context_manager_used():
    """Test that uow context manager is properly used"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_auth_service = Mock()

    valid_token = "valid_token"
    tg_name = "test_user"

    mock_auth_service.get_tg_name_from_token.return_value = tg_name
    mock_user_repo.get_by_tg_name.return_value = Mock(id=1)

    authenticate_use_case = AuthenticateUser(mock_uow, mock_user_repo, mock_auth_service)

    # Act
    asyncio.run(authenticate_use_case.execute(valid_token))

    # Assert
    mock_uow.__aenter__.assert_called_once()
    mock_uow.__aexit__.assert_called_once()


def test_execute_different_tg_names():
    """Test authentication with different telegram names"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_auth_service = Mock()

    test_cases = [
        ("token1", "user1", 1),
        ("token2", "user_with_underscore", 2),
        ("token3", "UserWithCaps", 3),
    ]

    authenticate_use_case = AuthenticateUser(mock_uow, mock_user_repo, mock_auth_service)

    for token, tg_name, user_id in test_cases:
        # Reset mocks for each test case
        mock_auth_service.reset_mock()
        mock_user_repo.reset_mock()

        mock_auth_service.get_tg_name_from_token.return_value = tg_name
        mock_user_repo.get_by_tg_name.return_value = Mock(id=user_id)

        # Act
        result = asyncio.run(authenticate_use_case.execute(token))

        # Assert
        mock_auth_service.get_tg_name_from_token.assert_called_once_with(token)
        mock_user_repo.get_by_tg_name.assert_called_once_with(tg_name)
        assert result == user_id


def test_execute_repository_raises_exception():
    """Test behavior when repository raises an exception"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_auth_service = Mock()

    valid_token = "valid_token"
    tg_name = "test_user"

    mock_auth_service.get_tg_name_from_token.return_value = tg_name
    mock_user_repo.get_by_tg_name.side_effect = Exception("Database error")

    authenticate_use_case = AuthenticateUser(mock_uow, mock_user_repo, mock_auth_service)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        asyncio.run(authenticate_use_case.execute(valid_token))

    assert "Database error" in str(exc_info.value)
    mock_auth_service.get_tg_name_from_token.assert_called_once_with(valid_token)
    mock_user_repo.get_by_tg_name.assert_called_once_with(tg_name)


def test_execute_auth_service_raises_exception():
    """Test behavior when auth service raises an exception"""
    # Arrange
    mock_uow = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_auth_service = Mock()

    valid_token = "valid_token"
    mock_auth_service.get_tg_name_from_token.side_effect = Exception("Token validation failed")

    authenticate_use_case = AuthenticateUser(mock_uow, mock_user_repo, mock_auth_service)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        asyncio.run(authenticate_use_case.execute(valid_token))

    assert "Token validation failed" in str(exc_info.value)
    mock_auth_service.get_tg_name_from_token.assert_called_once_with(valid_token)
    mock_user_repo.get_by_tg_name.assert_not_called()


def test_execute_successful_authentication():
    """Test successful authentication when user owns the task"""
    # Arrange
    mock_uow = AsyncMock()
    mock_task_repo = AsyncMock()

    task_id = 123
    user_id = 42  # AuthenticatedUserId is NewType of int

    # Create a mock task owned by the user
    mock_task = Mock()
    mock_task.user_id = user_id

    mock_task_repo.get_by_id.return_value = mock_task

    authenticate_use_case = AuthenticateTaskOwner(mock_uow, mock_task_repo)

    # Act
    result = asyncio.run(authenticate_use_case.execute(task_id, user_id))

    # Assert
    mock_task_repo.get_by_id.assert_called_once_with(task_id)
    # Result should be AuthenticatedOwnerId which is NewType of user_id
    assert result == user_id


def test_execute_task_not_found():
    """Test authentication fails when task doesn't exist"""
    # Arrange
    mock_uow = AsyncMock()
    mock_task_repo = AsyncMock()

    task_id = 999
    user_id = 42

    mock_task_repo.get_by_id.return_value = None

    authenticate_use_case = AuthenticateTaskOwner(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(UndefinedTaskError) as exc_info:
        asyncio.run(authenticate_use_case.execute(task_id, user_id))

    assert "Unable to find task" in str(exc_info.value)
    assert exc_info.value.status == 404

    mock_task_repo.get_by_id.assert_called_once_with(task_id)


def test_execute_user_not_owner():
    """Test authentication fails when user doesn't own the task"""
    # Arrange
    mock_uow = AsyncMock()
    mock_task_repo = AsyncMock()

    task_id = 123
    requesting_user_id = 42
    task_owner_id = 99  # Different user

    mock_task = Mock()
    mock_task.user_id = task_owner_id

    mock_task_repo.get_by_id.return_value = mock_task

    authenticate_use_case = AuthenticateTaskOwner(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(HasNoAccessError) as exc_info:
        asyncio.run(authenticate_use_case.execute(task_id, requesting_user_id))

    assert "User has no access the task" in str(exc_info.value)
    assert exc_info.value.status == 403

    mock_task_repo.get_by_id.assert_called_once_with(task_id)


def test_execute_uow_context_manager_used():
    """Test that uow context manager is properly used"""
    # Arrange
    mock_uow = AsyncMock()
    mock_task_repo = AsyncMock()

    task_id = 123
    user_id = 42

    mock_task = Mock()
    mock_task.user_id = user_id
    mock_task_repo.get_by_id.return_value = mock_task

    authenticate_use_case = AuthenticateTaskOwner(mock_uow, mock_task_repo)

    # Act
    asyncio.run(authenticate_use_case.execute(task_id, user_id))

    # Assert
    mock_uow.__aenter__.assert_called_once()
    mock_uow.__aexit__.assert_called_once()


def test_execute_different_task_ids():
    """Test authentication with different task IDs"""
    # Arrange
    mock_uow = AsyncMock()
    mock_task_repo = AsyncMock()

    test_cases = [
        (1, 42),   # task_id, user_id
        (999, 100),
        (0, 1),    # Edge cases
        (-1, 5),   # Negative task_id (if allowed)
    ]

    for task_id, user_id in test_cases:
        # Reset mocks for each test
        mock_uow.reset_mock()
        mock_task_repo.reset_mock()

        mock_task = Mock()
        mock_task.user_id = user_id
        mock_task_repo.get_by_id.return_value = mock_task

        authenticate_use_case = AuthenticateTaskOwner(mock_uow, mock_task_repo)

        # Act
        result = asyncio.run(authenticate_use_case.execute(task_id, user_id))

        # Assert
        mock_task_repo.get_by_id.assert_called_once_with(task_id)
        assert result == user_id


def test_execute_repository_raises_exception():
    """Test behavior when repository raises an exception"""
    # Arrange
    mock_uow = AsyncMock()
    mock_task_repo = AsyncMock()

    task_id = 123
    user_id = 42

    mock_task_repo.get_by_id.side_effect = Exception("Database error")

    authenticate_use_case = AuthenticateTaskOwner(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        asyncio.run(authenticate_use_case.execute(task_id, user_id))

    assert "Database error" in str(exc_info.value)
    mock_task_repo.get_by_id.assert_called_once_with(task_id)


def test_execute_task_user_id_matches_exact_value():
    """Test that user_id comparison is exact (not just truthy/falsy)"""
    # Arrange
    mock_uow = AsyncMock()
    mock_task_repo = AsyncMock()

    task_id = 123
    user_id = 0  # user_id can be 0!

    mock_task = Mock()
    mock_task.user_id = 0  # Must match exactly

    mock_task_repo.get_by_id.return_value = mock_task

    authenticate_use_case = AuthenticateTaskOwner(mock_uow, mock_task_repo)

    # Act
    result = asyncio.run(authenticate_use_case.execute(task_id, user_id))

    # Assert
    mock_task_repo.get_by_id.assert_called_once_with(task_id)
    assert result == user_id  # Should work even with user_id = 0


def test_execute_task_user_id_different_but_falsy():
    """Test authentication fails when user_id differs even if both are falsy"""
    # Arrange
    mock_uow = AsyncMock()
    mock_task_repo = AsyncMock()

    task_id = 123
    requesting_user_id = 0
    task_owner_id = 1  # Different (truthy)

    mock_task = Mock()
    mock_task.user_id = task_owner_id

    mock_task_repo.get_by_id.return_value = mock_task

    authenticate_use_case = AuthenticateTaskOwner(mock_uow, mock_task_repo)

    # Act & Assert
    with pytest.raises(HasNoAccessError) as exc_info:
        asyncio.run(authenticate_use_case.execute(task_id, requesting_user_id))

    assert "User has no access the task" in str(exc_info.value)
    mock_task_repo.get_by_id.assert_called_once_with(task_id)
