from typing import Self, Protocol, TypeVar


class HasId(Protocol):
    id: int


DomainEnt = TypeVar("DomainEnt", bound=HasId)


class UoWInterface(Protocol):
    """
    UoW that manages transaction starting when enter the context. Management of transaction going on automatically
    that mean commit will be called after exit from context or rollback if exception will be raised inside context.
    """

    async def __aenter__(self) -> Self: ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool: ...

    def save(self, *ents: DomainEnt) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def flush(self) -> None: ...
    def in_transaction(self) -> bool: ...
