from sqlalchemy import (
    Table, Column, String,
    ForeignKey, DateTime
)
from .base import metadata, id_


tasks = Table(
    "tasks", metadata,
    id_(),
    Column("title", String, nullable=False),
    Column("description", String, nullable=True),
    Column("deadline", DateTime(timezone=True), nullable=False),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("creation_date", DateTime(timezone=True), nullable=False),
    Column("pass_date", DateTime(timezone=True), nullable=True),
    Column("parent_id", ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
)
