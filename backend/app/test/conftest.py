from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import ASGITransport, AsyncClient
import pytest
import uuid

from app.infrastructure.database import Base, get_db
from app.main import app
from app.core import settings

TEST_DB_URL = settings.TEST_DB_URL

@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    yield engine #Give value of engine (wait/yield) then dispose
    await engine.dispose()

@pytest.fixture(scope="session")
async def db_engine_factory(db_engine):
    return async_sessionmaker(db_engine, expire_on_commit=False)

@pytest.fixture(scope="session", autouse=True)
async def init_db(db_engine):
    """Create table once before test run"""
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(db_engine_factory) -> AsyncGenerator[AsyncSession, None]:
    """Get a fresh DB session for each test"""
    async with db_engine_factory() as session:
        yield session

@pytest.fixture
async def client(session) -> AsyncGenerator[AsyncClient, None]:
    """Fake API client that overrides DB dependency"""

    async def override_get_db():
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
    
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url = "http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

# Mocking Auth

from app.infrastructure.security import get_current_user, AuthenticatedUser
from app.features.users.models import User

TEST_USER_ID = uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")

@pytest.fixture(scope="session")
async def test_user(db_engine_factory):
    """Insert a test user into the database"""
    async with db_engine_factory() as  session:
        user = User(
            id=TEST_USER_ID,
            supabase_user_id="supabase-test-user-id",
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_email_verified=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
@pytest.fixture
async def mock_user_token(client, test_user):
    """Forces the API to think we are logged in"""
    user = AuthenticatedUser(
        user_id=str(test_user.id),
        email=test_user.email,
        role="user",
        raw_payload={}
    )

    app.dependency_overrides[get_current_user] = lambda: user
    yield user





