from src.domain.exc import DomainError


class UnfinishedTaskError(DomainError):
    pass


class HasNoDirectAccessError(DomainError):
    pass
