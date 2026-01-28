from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from src.domain.entities import Task


class TaskCreateDTO(BaseModel):
    title: str
    description: str
    deadline: datetime
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
    subtasks: list["TaskPreviewDTO"]

    model_config = ConfigDict(from_attributes=True)


class PaginatedTasksDTO(BaseModel):
    tasks: list[TaskViewDTO]
    prev_page: Optional[int]
    next_page: Optional[int]


class TaskPreviewDTO(BaseModel):
    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)


class TaskViewForUserDTO(BaseModel):
    id: int
    title: str
    description: str
    creation_date: datetime
    deadline: datetime
    pass_date: Optional[datetime] = None
    parent_id: Optional[int] = None
    subtasks: list['TaskViewForUserDTO'] = []
