from typing import Optional
from datetime import datetime, timezone, timedelta

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(max_length=100)
    description: str = Field(max_length=500)
    creation_date: datetime
    deadline: datetime
    user_id: int
    task_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(max_length=100, default=None)
    description: Optional[str] = Field(max_length=500, default=None)
    deadline: Optional[datetime] = None
    user_id: Optional[int] = None
    task_id: Optional[int] = None


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


class TaskViewForUser(BaseModel):
    id: int
    title: str
    description: str
    creation_date: datetime
    deadline: datetime
    pass_date: Optional[datetime]
    task_id: Optional[int]
    subtasks: list['TaskViewForUser']

    class Config:
        orm_mode = True


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
