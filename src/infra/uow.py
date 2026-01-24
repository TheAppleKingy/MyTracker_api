from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction
from src.application.interfaces.uow import UoWInterface, DomainEnt
from src.logger import logger


class AlchemyUoW(UoWInterface):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._t: AsyncSessionTransaction = None  # type: ignore

    async def __aenter__(self) -> Self:
        # logger.critical(f"{self._session.in_transaction()}, {self._session.get_transaction()}")
        self._t = await self._session.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._t:
            if exc_type is not None:
                await self._t.rollback()
            else:
                await self._t.commit()
        self._t = None  # type: ignore
        return False

    async def commit(self) -> None:
        if self._t:
            await self._t.commit()

    async def rollback(self) -> None:
        if self._t:
            await self._t.rollback()

    async def flush(self) -> None:
        return await self._session.flush()

    def save(self, *ents: DomainEnt):
        return self._session.add_all(ents)

    def in_transaction(self) -> bool:
        return self._session.in_transaction()
