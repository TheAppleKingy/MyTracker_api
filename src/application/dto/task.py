from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class TaskCreateDTO(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    parent_id: Optional[int] = None


class TaskUpdateDTO(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None


class TaskViewDTO(BaseModel):
    id: int
    title: str
    description: str
    creation_date: datetime
    deadline: datetime
    pass_date: Optional[datetime] = None
    parent_id: Optional[int] = None
    subtasks: list["TaskPreviewDTO"] = []


class TaskPreviewDTO(BaseModel):
    id: int
    title: str


class TaskViewForUserDTO(BaseModel):
    id: int
    title: str
    description: str
    creation_date: datetime
    deadline: datetime
    pass_date: Optional[datetime] = None
    parent_id: Optional[int] = None
    subtasks: list['TaskViewForUserDTO'] = []
