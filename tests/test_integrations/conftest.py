# import pytest
# import pytest_asyncio
# import os
# import asyncpg

# from datetime import datetime, timezone, timedelta

# from sqlalchemy import select
# from sqlalchemy.orm import selectinload
# from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncEngine, AsyncSession

# from src.infra.configs import DBConfig
# from src.infra.db.tables.base import metadata
# from src.domain.entities import User, Task

# db_conf = DBConfig()
# init_test_query = f"CREATE DATABASE {db_conf.postgres_db}"
# close_test_query = f"DROP DATABASE IF EXISTS {db_conf.postgres_db}"


# @pytest_asyncio.fixture(scope="session", autouse=True)
# async def prepare_database():
#     admin_conn = await asyncpg.connect(db_conf.formatted_conn_url)
#     await admin_conn.execute(f"DROP DATABASE IF EXISTS {db_conf.postgres_db} WITH (FORCE)")
#     await admin_conn.execute(f"CREATE DATABASE {db_conf.postgres_db}")
#     await admin_conn.close()
#     engine = create_async_engine(db_conf.conn_url, echo=False)
#     async with engine.begin() as conn:
#         await conn.run_sync(metadata.create_all())
#     yield
#     await engine.dispose()
#     admin_conn = await asyncpg.connect(db_conf.formatted_conn_url)
#     await admin_conn.execute(f"DROP DATABASE IF EXISTS {db_conf.postgres_db} WITH (FORCE)")
#     await admin_conn.close()


# @pytest_asyncio.fixture
# async def engine():
#     engine = create_async_engine(db_conf.conn_url, echo=False)
#     yield engine
#     await engine.dispose()


# @pytest_asyncio.fixture
# async def session(engine: AsyncEngine):
#     session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
#     async with session_maker() as session:
#         for table in reversed(metadata.sorted_tables):
#             await session.execute(table.delete())
#         await session.commit()
#         yield session
#         await session.rollback()


# @pytest_asyncio.fixture(autouse=True)
# async def setup(session: AsyncSession):
#     user = User(tg_name='simple_user')
#     session.add(user)
#     await session.flush()
#     task1 = Task(title='t1', description='t1', user_id=user.id,
#                  deadline=datetime.now(timezone.utc)+timedelta(days=7))
#     sub1 = Task(title='s1', description='s1', parent=task1, user_id=user.id,
#                 deadline=datetime.now(timezone.utc)+timedelta(days=6))
#     session.add(task1)
#     user.tasks = [task1]
#     await session.commit()


# @pytest.fixture
# def user_repo(session: AsyncSession):
#     return UserRepoFactory.get_user_repository(session)


# @pytest.fixture
# def task_repo(session: AsyncSession):
#     return TaskRepoFactory.get_task_repository(session)


# @pytest_asyncio.fixture
# async def simple_user(session: AsyncSession):
#     query = select(User).where(User.tg_name == 'simple_user')
#     res = await session.execute(query)
#     user = res.scalar_one_or_none()
#     return user


# @pytest_asyncio.fixture
# async def task1(session: AsyncSession):
#     res = await session.execute(select(Task).where(Task.title == 't1').options(selectinload(Task.subtasks)))
#     return res.scalar_one()
