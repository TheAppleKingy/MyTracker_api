from src.domain.exc import DomainError


class UnfifnishedTaskError(DomainError):
    pass


class HasNoDirectAccessError(DomainError):
    pass
