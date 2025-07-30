from abc import ABC, abstractmethod

from sqlalchemy.sql.expression import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.users import User


class AbstractUserRepository(ABC):
    def __init__(self, session: AsyncSession):
        self.session = session

    @abstractmethod
    async def get_user(self, id: int) -> User | None: ...

    @abstractmethod
    async def get_user_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_user_and_tasks(self, id: int) -> User | None: ...

    @abstractmethod
    async def get_users_by(
        self, *conditions: ColumnElement[bool]) -> list[User]: ...

    @abstractmethod
    async def create_user(self, **user_data: dict) -> User: ...

    @abstractmethod
    async def delete_user(self, id: int) -> User: ...

    @abstractmethod
    async def update_user(self, id: int, **kwargs) -> User: ...
