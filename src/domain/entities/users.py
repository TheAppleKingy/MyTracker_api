from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .tasks import Base


if TYPE_CHECKING:
    from .tasks import Task


class User(Base):
    __tablename__ = 'users'
    tg_name: Mapped[str] = mapped_column(
        String(50), unique=True)
    email: Mapped[str] = mapped_column(
        String(50), unique=True)
    password: Mapped[str] = mapped_column()
    first_name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False)
    tasks: Mapped[list['Task']] = relationship(
        back_populates='user', cascade='all, delete-orphan', lazy='selectin')
