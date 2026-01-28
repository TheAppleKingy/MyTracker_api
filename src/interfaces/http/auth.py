from fastapi import APIRouter, Query
from dishka.integrations.fastapi import FromDishka, DishkaRoute

from src.application.dto.users import RegisterUserDTO
from src.application.use_cases import RegisterUser, CheckUserExists

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
    return await use_case.execute(dto)


@auth_router.get("/check")
async def check_user_registered(
    use_case: FromDishka[CheckUserExists],
    tg_name: str = Query()
):
    return await use_case.execute(tg_name)
