from sqlalchemy import (
    Table, Column, String,
    ForeignKey, Boolean
)
from .base import metadata, id_

users = Table(
    "users", metadata,
    id_(),
    Column("tg_name", String, unique=True, index=True, nullable=False),
    Column("password", String, nullable=False)
)
