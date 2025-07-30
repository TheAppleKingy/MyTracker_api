from fastapi import FastAPI


app = FastAPI()


def include_routers():
    from interfaces.api.routing.auth_routs import profile_router
    from interfaces.api.routing.api_for_bot import bot_router
    app.include_router(profile_router)
    app.include_router(bot_router)


def include_exc_handlers():
    from interfaces.api.exc_handlers import (
        service_error_handler,
        permission_error_handler,
        auth_error_handler,
    )
    from application.service.exceptions import UserPermissionServiceError, ServiceError, UserAuthServiceError
    app.add_exception_handler(ServiceError, service_error_handler)
    app.add_exception_handler(
        UserPermissionServiceError, permission_error_handler)
    app.add_exception_handler(UserAuthServiceError, auth_error_handler)


include_routers()
include_exc_handlers()
