from fastapi import APIRouter
from dishka.integrations.fastapi import FromDishka, DishkaRoute

from src.application.dto.users import RegisterUserDTO
from src.application.use_cases import RegisterUser

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
