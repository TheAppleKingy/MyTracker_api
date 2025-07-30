from typing import Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    tg_name: str = Field(max_length=50)
    email: str = Field(max_length=50)
    first_name: Optional[str] = Field(max_length=100, default=None)
    last_name: Optional[str] = Field(max_length=100, default=None)
    password: str = Field(max_length=25)


class UserView(BaseModel):
    id: Optional[int] = Field(default=None)
    tg_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)


class UserUpdate(BaseModel):
    tg_name: Optional[str] = Field(max_length=50, default=None)
    email: Optional[str] = Field(max_length=50, default=None)
    first_name: Optional[str] = Field(max_length=100, default=None)
    last_name: Optional[str] = Field(max_length=100, default=None)
    is_active: Optional[bool] = None


class Login(BaseModel):
    email: str
    password: str


class UserInGroup(BaseModel):
    id: int


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


class CheckIsActive(BaseModel):
    tg_name: str
