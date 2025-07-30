from typing import Annotated

from sqlalchemy import Integer, MetaData
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs


intpk = Annotated[int, mapped_column(
    primary_key=True, index=True, autoincrement=True)]


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True
    type_annotation_map = {
        intpk: Integer
    }
    id: Mapped[int] = mapped_column(
        unique=True, primary_key=True, autoincrement=True)

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self):
        cols = [
            f'{col} = {getattr(self, col)}' for idx, col in enumerate(self.__table__.columns.keys())
            if col in self.repr_cols or idx < self.repr_cols_num
        ]
        return f"<{self.__class__.__name__} {', '.join(cols)}>"
