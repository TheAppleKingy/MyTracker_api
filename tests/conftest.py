import pytest
import pytest_asyncio
import os
import asyncpg

from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncEngine, AsyncSession

from config import FORMATTED_DATABASE_URL, TEST_DATABASE_URL
from infra.db.tables.base import Base
from domain.entities.users import User
from domain.entities.tasks import Task
from infra.security.password_utils import hash_password
from infra.db.repository.factories import UserRepoFactory, TaskRepoFactory


test_db_name = os.getenv('TEST_DB_NAME')
init_test_query = f"CREATE DATABASE {test_db_name}"
close_test_query = f"DROP DATABASE IF EXISTS {test_db_name}"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    admin_conn = await asyncpg.connect(FORMATTED_DATABASE_URL)
    await admin_conn.execute(f"DROP DATABASE IF EXISTS {test_db_name} WITH (FORCE)")
    await admin_conn.execute(f"CREATE DATABASE {test_db_name}")
    await admin_conn.close()
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    admin_conn = await asyncpg.connect(FORMATTED_DATABASE_URL)
    await admin_conn.execute(f"DROP DATABASE IF EXISTS {test_db_name} WITH (FORCE)")
    await admin_conn.close()


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine):
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_maker() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()
        yield session
        await session.rollback()


@pytest_asyncio.fixture(autouse=True)
async def setup(session: AsyncSession):
    admin = User(tg_name='admin', email='admin@mail.ru',
                 password=hash_password('test_password'), is_active=True)
    simple_user = User(tg_name='simple_user', email='simple@mail.ru',
                       password=hash_password('test_password'), is_active=True)
    session.add_all([admin, simple_user])
    await session.flush()
    task1 = Task(title='t1', description='t1',
                 task_id=None, user_id=simple_user.id, creation_date=datetime.now(timezone.utc), deadline=datetime.now(timezone.utc)+timedelta(days=7))
    session.add(task1)
    await session.flush()
    sub1 = Task(title='s1', description='s1',
                task_id=task1.id, user_id=simple_user.id, creation_date=datetime.now(timezone.utc), deadline=datetime.now(timezone.utc)+timedelta(days=7))
    session.add_all([task1, sub1])
    await session.commit()


@pytest.fixture
def user_repo(session: AsyncSession):
    return UserRepoFactory.get_user_repository(session)


@pytest.fixture
def task_repo(session: AsyncSession):
    return TaskRepoFactory.get_task_repository(session)


@pytest_asyncio.fixture
async def simple_user(session: AsyncSession):
    query = select(User).where(User.tg_name == 'simple_user')
    res = await session.execute(query)
    user = res.scalar_one_or_none()
    return user


@pytest_asyncio.fixture
async def task1(session: AsyncSession):
    res = await session.execute(select(Task).where(Task.title == 't1').options(selectinload(Task.subtasks)))
    return res.scalar_one()
