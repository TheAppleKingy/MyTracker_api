from src.application.exc import ApplicationError


class UndefinedUserError(ApplicationError):
    pass


class InvalidUserPasswordError(ApplicationError):
    pass


class UserExistsError(ApplicationError):
    pass
