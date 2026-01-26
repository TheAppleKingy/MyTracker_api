from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.users import User
from src.application.interfaces.repositories import UserRepositoryInterface


class AlchemyUserRepository(UserRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_tg_name(self, tg_name: str) -> Optional[User]:
        return await self._session.scalar(select(User).where(User.tg_name == tg_name))

    async def count_by_tg_name(self, tg_name: str) -> int:
        return await self._session.scalar(select(func.count(User.id)).where(User.tg_name == tg_name)) or 0
