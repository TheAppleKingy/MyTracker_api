from abc import ABC, abstractmethod


class AbstractTokenHandler(ABC):
    @abstractmethod
    def encode(self, payload: dict) -> str: ...

    @abstractmethod
    def decode(self, token: str) -> dict: ...
