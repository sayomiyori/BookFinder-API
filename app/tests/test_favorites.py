"""Тесты эндпоинтов избранного."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_favorites_list_requires_auth(client: AsyncClient):
    """GET /users/me/favorites без токена — 401."""
    resp = await client.get("/api/v1/users/me/favorites")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_favorites_list_empty(client: AsyncClient, auth_headers: dict):
    """Список избранного пустой после регистрации."""
    resp = await client.get("/api/v1/users/me/favorites", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_favorites_add_and_list(client: AsyncClient, auth_headers: dict):
    """Добавление книги в избранное и появление в списке."""
    # Создаём книгу
    create = await client.post(
        "/api/v1/books",
        headers=auth_headers,
        json={"google_books_id": "fav-book-1", "title": "Favorite Book"},
    )
    assert create.status_code == 201
    book_id = create.json()["id"]

    # Добавляем в избранное
    add = await client.post(
        f"/api/v1/users/me/favorites/{book_id}",
        headers=auth_headers,
    )
    assert add.status_code == 201

    # Список избранного содержит книгу
    list_resp = await client.get("/api/v1/users/me/favorites", headers=auth_headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1
    assert list_resp.json()["items"][0]["book"]["id"] == book_id


@pytest.mark.asyncio
async def test_favorites_add_twice_400(client: AsyncClient, auth_headers: dict):
    """Повторное добавление той же книги — 400."""
    create = await client.post(
        "/api/v1/books",
        headers=auth_headers,
        json={"google_books_id": "fav-dup-1", "title": "Dup Book"},
    )
    book_id = create.json()["id"]
    await client.post(f"/api/v1/users/me/favorites/{book_id}", headers=auth_headers)
    resp = await client.post(f"/api/v1/users/me/favorites/{book_id}", headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_favorites_remove_ok(client: AsyncClient, auth_headers: dict):
    """Удаление из избранного — 204, затем список пустой."""
    create = await client.post(
        "/api/v1/books",
        headers=auth_headers,
        json={"google_books_id": "fav-rem-1", "title": "To Remove"},
    )
    book_id = create.json()["id"]
    await client.post(f"/api/v1/users/me/favorites/{book_id}", headers=auth_headers)

    resp = await client.delete(
        f"/api/v1/users/me/favorites/{book_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 204

    list_resp = await client.get("/api/v1/users/me/favorites", headers=auth_headers)
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_favorites_remove_not_found(client: AsyncClient, auth_headers: dict):
    """DELETE из избранного несуществующей записи — 404."""
    resp = await client.delete(
        "/api/v1/users/me/favorites/99999",
        headers=auth_headers,
    )
    assert resp.status_code == 404
