from sqlalchemy import select, insert, delete, update
from sqlalchemy.sql.expression import ColumnElement
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from domain.entities.users import User
from domain.repositories.user_repository import AbstractUserRepository
from domain.repositories.exceptions import UserRepositoryError, parse_integrity_err_message

from .auto_commit import commitable


class UserRepository(AbstractUserRepository):
    async def get_user(self, id: int) -> User | None:
        return await self.session.scalar(select(User).where(User.id == id))

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def get_user_and_tasks(self, id: int) -> User | None:
        return await self.session.scalar(select(User).where(User.id == id).options(selectinload(User.tasks)))

    async def get_users_by(self, *conditions: ColumnElement[bool]) -> list[User]:
        db_resp = await self.session.scalars(select(User).where(*conditions))
        return db_resp.all()

    @commitable
    async def create_user(self, **user_data: dict) -> User:
        try:
            return await self.session.scalar(insert(User).values(**user_data).returning(User))
        except SQLAlchemyError as e:
            msg = str(e)
            if isinstance(e, IntegrityError):
                key, val = parse_integrity_err_message(msg)
                msg = f'User with {key} {val} already exists'
            raise UserRepositoryError(msg)

    @commitable
    async def delete_user(self, id: int) -> User:
        return await self.session.scalar(delete(User).where(User.id == id).returning(User))

    @commitable
    async def update_user(self, id: int, **kwargs) -> User:
        try:
            return await self.session.scalar(update(User).values(**kwargs).returning(User))
        except SQLAlchemyError as e:
            msg = str(e)
            if isinstance(e, IntegrityError):
                key, val = parse_integrity_err_message(msg)
                msg = f'User with {key} {val} already exists'
            raise UserRepositoryError(msg)
