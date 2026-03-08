"""Тесты эндпоинтов книг."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_search_books_requires_q(client: AsyncClient):
    """GET /books без q — 422."""
    resp = await client.get("/api/v1/books")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_books_ok(client: AsyncClient):
    """Поиск с q возвращает 200 и структуру с items, total, page, limit."""
    with patch("app.api.v1.books.fetch_books_from_google", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/api/v1/books?q=python&page=1&limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["limit"] == 5
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_book_not_found(client: AsyncClient):
    """GET /books/99999 — 404."""
    resp = await client.get("/api/v1/books/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_book_requires_auth(client: AsyncClient):
    """POST /books без токена — 401."""
    resp = await client.post(
        "/api/v1/books",
        json={
            "google_books_id": "manual-1",
            "title": "Test Book",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_book_ok(client: AsyncClient, auth_headers: dict):
    """POST /books с токеном — 201 и объект книги."""
    resp = await client.post(
        "/api/v1/books",
        headers=auth_headers,
        json={
            "google_books_id": "manual-test-1",
            "title": "Ручная тестовая книга",
            "authors": ["Автор"],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Ручная тестовая книга"
    assert data["google_books_id"] == "manual-test-1"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_book_ok(client: AsyncClient, auth_headers: dict):
    """GET /books/{id} возвращает созданную книгу."""
    create = await client.post(
        "/api/v1/books",
        headers=auth_headers,
        json={"google_books_id": "get-test-1", "title": "Book to Get"},
    )
    assert create.status_code == 201
    book_id = create.json()["id"]
    resp = await client.get(f"/api/v1/books/{book_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == book_id
    assert resp.json()["title"] == "Book to Get"
