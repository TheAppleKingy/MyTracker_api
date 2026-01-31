from typing import AsyncGenerator

from dishka import Provider, provide, Scope, make_async_container
from dishka.integrations.fastapi import FastapiProvider
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine
)
from fastapi import Request

from src.application.use_cases import *
from src.application.interfaces.repositories import *
from src.application.interfaces.services import *
from src.application.interfaces.uow import UoWInterface
from src.infra.configs import (
    DBConfig,
    AppConfig
)
from src.infra.repository import *
from src.infra.services import *
from src.infra.uow import AlchemyUoW
from src.domain.types import AuthenticatedUserId, AuthenticatedOwnerId


class DBProvider(Provider):
    scope = Scope.APP

    @provide
    def get_db_conf(self) -> DBConfig:
        return DBConfig()  # type: ignore

    @provide
    def get_engine(self, config: DBConfig) -> AsyncEngine:
        return create_async_engine(config.conn_url)

    @provide
    def get_sessionmaker(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            engine,
            expire_on_commit=False,
            autoflush=False,
            autobegin=False
        )

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self,
        sessionmaker: async_sessionmaker[AsyncSession]
    ) -> AsyncGenerator[AsyncSession, None]:
        async with sessionmaker() as session:
            try:
                yield session
            finally:
                await session.close()

    @provide(scope=Scope.REQUEST)
    def get_uow(self, session: AsyncSession) -> UoWInterface:
        return AlchemyUoW(session)


repo_provider = Provider(scope=Scope.REQUEST)
repo_provider.provide(AlchemyTaskRepository, provides=TaskRepositoryInterface)
repo_provider.provide(AlchemyUserRepository, provides=UserRepositoryInterface)


class ServiceProvider(Provider):
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    def get_app_conf(self) -> AppConfig:
        return AppConfig()  # type: ignore

    @provide
    def get_auth_service(self, conf: AppConfig) -> AuthenticationServiceInterface:
        return JWTAuthenticationService(conf.secret)


use_case_provider = Provider(scope=Scope.REQUEST)
use_case_provider.provide_all(
    RegisterUser,
    CheckUserExists,
    CheckTaskActive,
    AuthenticateUser,
    ShowParentId,
    ShowTask,
    ShowTasks,
    ShowSubtasks,
    CreateTask,
    UpdateTask,
    DeleteTask,
    FinishTask,
    ForceFinishTask,
    AuthenticateTaskOwner
)


class AuthProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def auth_user(self, r: Request, use_case: AuthenticateUser) -> AuthenticatedUserId:
        return await use_case.execute(r.cookies.get("token"))

    @provide
    async def auth_owner(
        self,
        r: Request,
        use_case: AuthenticateTaskOwner,
        user_id: AuthenticatedUserId
    ) -> AuthenticatedOwnerId:
        return await use_case.execute(int(r.path_params.get("task_id")), user_id)  # type: ignore


container = make_async_container(
    DBProvider(),
    repo_provider,
    ServiceProvider(),
    use_case_provider,
    AuthProvider(),
    FastapiProvider()
)
