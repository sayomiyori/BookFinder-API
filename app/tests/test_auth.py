"""Тесты эндпоинтов аутентификации."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_ok(client: AsyncClient):
    """Регистрация возвращает 200 и токен."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "secret123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Повторная регистрация с тем же email — 400."""
    payload = {"email": "dup@example.com", "password": "secret123"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400
    assert "уже зарегистрирован" in resp.json().get("detail", "")


@pytest.mark.asyncio
async def test_login_ok(client: AsyncClient):
    """Вход по email и паролю — 200 и токен."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "mypass123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "mypass123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Неверный пароль — 401."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrong@example.com", "password": "right123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "badpass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_ok(client: AsyncClient, auth_headers: dict):
    """GET /me с токеном — 200 и данные пользователя."""
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "testuser@example.com"
    assert "id" in data
    assert "is_active" in data


@pytest.mark.asyncio
async def test_me_unauthorized(client: AsyncClient):
    """GET /me без токена — 401."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
