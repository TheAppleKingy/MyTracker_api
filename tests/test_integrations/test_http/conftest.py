import pytest
import pytest_asyncio

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from infra.db.session import get_db_session
from app import app
from infra.security.token.factory import TokenHandlerFactory
from domain.entities.users import User


@pytest_asyncio.fixture
async def client(session: AsyncSession):
    app.dependency_overrides[get_db_session] = lambda: session
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(client: AsyncClient, admin_user: User):
    jwt_handler = TokenHandlerFactory.get_jwt_handler()
    token = jwt_handler.get_token_for_user(admin_user)
    client.cookies.set('token', token, domain='test.local')
    return client


@pytest.fixture
def simple_client(client: AsyncClient, simple_user: User):
    jwt_handler = TokenHandlerFactory.get_jwt_handler()
    token = jwt_handler.get_token_for_user(simple_user)
    client.cookies.set('token', token, domain='test.local')
    return client
