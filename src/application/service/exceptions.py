class ServiceError(Exception):
    ...


class TaskServiceError(ServiceError):
    ...


class UserPermissionServiceError(ServiceError):
    ...


class UserAuthDataServiceError(ServiceError):
    ...


class UserAuthServiceError(ServiceError):
    ...


class GroupServiceError(ServiceError):
    ...
