from fastapi import status
from fastapi.requests import Request
from fastapi.exceptions import HTTPException

from application.service.exceptions import UserPermissionServiceError, UserAuthServiceError, ServiceError


def service_error_handler(request: Request, e: ServiceError):
    raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


def permission_error_handler(request: Request, e: UserPermissionServiceError):
    raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))


def auth_error_handler(request: Request, e: UserAuthServiceError):
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))
