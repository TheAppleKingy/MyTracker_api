from fastapi import APIRouter
from dishka.integrations.fastapi import FromDishka, DishkaRoute

from src.application.dto.users import LoginUserDTO, RegisterUserDTO
from src.application.use_cases import RegisterUser, LoginUser

auth_router = APIRouter(
    prefix='/auth',
    tags=['Auth'],
    route_class=DishkaRoute
)


@auth_router.post("/register")
async def register_user(
    dto: RegisterUserDTO,
    use_case: FromDishka[RegisterUser]
):
    return {"token": await use_case.execute(dto)}


@auth_router.post("/login")
async def login_user(
    dto: LoginUserDTO,
    use_case: FromDishka[LoginUser]
):
    return {"token": await use_case.execute(dto)}
