from fastapi import Depends, status, APIRouter

from application.dto.users_dto import UserCreate, ChangePassword, Login
from application.service.user import UserAuthDataService

from infra.security.token.factory import TokenHandlerFactory as handler_factory
from infra.security.permissions.permissions import IsActivePermission

from domain.entities.users import User

from ..responses import response_cookies
from ..dependencies import authenticate, check_permissions, get_user_auth_data_service


profile_router = APIRouter(
    prefix='/api/profile',
    tags=['Profile']
)


@profile_router.post('/login')
async def login(login_data: Login, auth_service: UserAuthDataService = Depends(get_user_auth_data_service)):
    user = await auth_service.login_user(login_data)
    jwt_handler = handler_factory.get_jwt_handler()
    token = jwt_handler.get_token_for_user(user)
    response = response_cookies({'detail': 'logged in'}, status.HTTP_200_OK, {
                                'token': token})
    return response


@profile_router.post('/logout')
async def logout(user: User = Depends(authenticate)):
    response = response_cookies(
        {'detail': 'logged out'}, status.HTTP_200_OK, cookies_data=['token'], delete=True)
    return response


@profile_router.post('/request/registration')
async def registration_request(reg_data: UserCreate, auth_service: UserAuthDataService = Depends(get_user_auth_data_service)):
    await auth_service.registration_request(reg_data)
    return response_cookies({'detail': 'we sent email on your mail for confirm registration'}, status=status.HTTP_200_OK)


@profile_router.get('/confirm/registration/{confirm_token}')
async def confirm_registration(confirm_token: str, auth_service: UserAuthDataService = Depends(get_user_auth_data_service)):
    await auth_service.confirm_registration(confirm_token)
    return response_cookies({'detail': 'registration confirmed!'}, status.HTTP_200_OK)


@profile_router.get('/request/change_password')
async def change_password_request(auth_service: UserAuthDataService = Depends(get_user_auth_data_service), request_user: User = Depends(check_permissions(IsActivePermission()))):
    await auth_service.change_password_request(request_user.id)
    return response_cookies({'detail': 'we sent email on your mail for confirm change password'}, status=status.HTTP_200_OK)


@profile_router.post('/confirm/change_password/{confirm_token}')
async def confirm_change_password(confirm_token: str, change_password_schema: ChangePassword, auth_service: UserAuthDataService = Depends(get_user_auth_data_service), request_user: User = Depends(check_permissions(IsActivePermission()))):
    await auth_service.confirm_change_password(confirm_token, change_password_schema)
    return response_cookies({'detail': 'password was change successfully'}, status.HTTP_200_OK)
