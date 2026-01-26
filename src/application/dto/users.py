from typing import Optional

from pydantic import BaseModel, Field


class RegisterUserDTO(BaseModel):
    tg_name: str


class TokenResponseDTO(BaseModel):
    token: str
