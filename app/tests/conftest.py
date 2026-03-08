"""
Фикстуры для тестов: тестовая БД (SQLite in-memory), клиент, токен.
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import AsyncGenerator as TypingAsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.main import app
from app.models import Base

# Тестовая БД в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Подмена get_db для тестов: сессия к in-memory SQLite."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Свежая сессия БД для теста; таблицы создаются и удаляются для изоляции."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Async HTTP-клиент с подменённой БД на тестовую сессию."""
    async def _get_test_db() -> TypingAsyncGenerator[AsyncSession, None]:
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _get_test_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    """Регистрация пользователя и заголовок Authorization с токеном."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "testuser@example.com", "password": "testpass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}
