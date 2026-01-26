from src.application.exc import ApplicationError


class UndefinedUserError(ApplicationError):
    pass


class UserExistsError(ApplicationError):
    pass


class UndefinedTaskError(ApplicationError):
    pass


class HasNoAccessError(ApplicationError):
    pass


class TaskAlreadyFinishedError(ApplicationError):
    pass
