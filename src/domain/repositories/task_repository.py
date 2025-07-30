from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.tasks import Task


class AbstractTaskRepository(ABC):
    def __init__(self, session: AsyncSession):
        self.session = session

    @abstractmethod
    async def get_task(self, id: int) -> Task | None: ...

    @abstractmethod
    async def get_root_tasks(self) -> list[Task]: ...

    @abstractmethod
    async def get_root_tasks_for_user(self, user_id: int) -> list[Task]: ...

    @abstractmethod
    async def create_task(self, **task_data) -> Task: ...

    @abstractmethod
    async def delete_task(self, id: int) -> Task: ...

    @abstractmethod
    async def update_task(self, id: int, **kwargs) -> Task: ...

    @abstractmethod
    async def get_nested_tasks(
        self, from_task_id: int, return_list: bool = False) -> Task | list[Task]: ...
