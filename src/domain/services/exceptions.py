from src.domain.exc import DomainError


class InvalidDeadlineError(DomainError):
    pass


class MaxDepthError(DomainError):
    pass


class ParentFinishedError(DomainError):
    pass
