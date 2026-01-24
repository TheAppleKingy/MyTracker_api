from typing import Protocol, Optional

from src.domain.entities.users import User


class UserRepositoryInterface(Protocol):
    async def get_by_tg_name(self, tg_name: str) -> Optional[User]: ...
    async def count_by_tg_name(self, tg_name: str) -> int: ...
