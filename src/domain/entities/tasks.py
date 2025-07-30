from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped, validates

from application.service.exceptions import TaskServiceError

from infra.db.tables.base import Base


if TYPE_CHECKING:
    from .users import User


class Task(Base):
    __tablename__ = 'tasks'
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500))
    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True))
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    pass_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True)
    user: Mapped['User'] = relationship(
        back_populates='tasks', lazy='selectin')
    user_id: Mapped[int] = mapped_column(ForeignKey(
        'users.id', ondelete='CASCADE'), index=True)
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True, index=True)
    task: Mapped['Task'] = relationship(
        remote_side='Task.id', back_populates='subtasks', lazy='selectin')
    subtasks: Mapped[list['Task']] = relationship(
        back_populates='task', cascade='all, delete-orphan', lazy='selectin')

    @validates('pass_date', 'deadline')
    def validate_dates(self, key, val):
        if val and val <= self.creation_date:
            raise TaskServiceError(
                f'Cannot set {key} with value less or equal creation_date')
        return val

    def is_root(self):
        return not bool(self.task_id)

    def is_done(self):
        return bool(self.pass_date)

    def finish(self):
        self.pass_date = datetime.now(timezone.utc)
