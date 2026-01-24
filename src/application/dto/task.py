from typing import Optional
from datetime import datetime, timezone, timedelta

from pydantic import BaseModel, Field


class TaskCreateDTO(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    parent_id: Optional[int] = None


class TaskUpdateDTO(BaseModel):
    title: Optional[str] = Field(max_length=100, default=None)
    description: Optional[str] = Field(max_length=500, default=None)
    deadline: Optional[datetime] = None


class TaskView(BaseModel):
    id: int
    title: str
    description: str
    creation_date: datetime
    deadline: datetime
    pass_date: Optional[datetime]
    user_id: int
    task_id: Optional[int] = None


class TaskTree(TaskView):
    subtasks: list['TaskTree']


class TaskViewForUserDTO(BaseModel):
    id: int
    title: str
    description: str
    creation_date: datetime
    deadline: datetime
    pass_date: Optional[datetime] = None
    parent_id: Optional[int] = None
    subtasks: list['TaskViewForUserDTO'] = []


class TaskCreateForUser(BaseModel):
    title: str = Field(max_length=100)
    description: str = Field(max_length=500)
    creation_date: datetime
    deadline: datetime
    task_id: Optional[int] = None


class TaskUpdateForUser(BaseModel):
    title: Optional[str] = Field(max_length=100, default=None)
    description: Optional[str] = Field(max_length=500, default=None)
    deadline: Optional[datetime] = None
    pass_date: Optional[datetime] = None
    task_id: Optional[int] = None
