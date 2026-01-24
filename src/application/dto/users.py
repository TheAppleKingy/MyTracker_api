from typing import Optional

from pydantic import BaseModel, Field


class RegisterUserDTO(BaseModel):
    tg_name: str
    password: str = Field(min_length=8)


class LoginUserDTO(BaseModel):
    tg_name: str
    password: str


class TokenResponseDTO(BaseModel):
    token: str


class ChangePasswordDTO(BaseModel):
    new_password: str = Field(min_length=8)
