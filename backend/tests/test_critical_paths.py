"""Tier 2 regression coverage for critical authentication and todo paths."""

import pytest
from httpx import AsyncClient


async def register_and_get_token(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_tampered_access_token_is_rejected(client: AsyncClient):
    """A token whose signature changes must not authenticate a request."""
    token = await register_and_get_token(client, "tampered-token@example.com")
    header, payload, signature = token.split(".")
    altered_signature = ("A" if signature[0] != "A" else "B") + signature[1:]

    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers(f"{header}.{payload}.{altered_signature}"),
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_user_cannot_read_update_or_delete_another_users_todo(
    client: AsyncClient,
):
    """A todo UUID must not grant another authenticated user access."""
    owner_headers = auth_headers(
        await register_and_get_token(client, "tier2-owner@example.com")
    )
    other_headers = auth_headers(
        await register_and_get_token(client, "tier2-other@example.com")
    )
    created = await client.post(
        "/api/v1/todos",
        headers=owner_headers,
        json={"title": "Owner only"},
    )
    todo_url = f"/api/v1/todos/{created.json()['id']}"

    assert (await client.get(todo_url, headers=other_headers)).status_code == 404
    assert (
        await client.put(
            todo_url,
            headers=other_headers,
            json={"title": "Attempted takeover"},
        )
    ).status_code == 404
    assert (await client.delete(todo_url, headers=other_headers)).status_code == 404
    assert (await client.get(todo_url, headers=owner_headers)).json()[
        "title"
    ] == "Owner only"


@pytest.mark.asyncio
async def test_todo_mutations_refresh_cached_list(client: AsyncClient):
    """Create, update, and delete must make the next list request current."""
    headers = auth_headers(
        await register_and_get_token(client, "tier2-cache@example.com")
    )

    assert (await client.get("/api/v1/todos", headers=headers)).json()["total"] == 0

    created = await client.post(
        "/api/v1/todos", headers=headers, json={"title": "Initial title"}
    )
    todo_id = created.json()["id"]
    list_after_create = await client.get("/api/v1/todos", headers=headers)
    assert list_after_create.json()["items"][0]["title"] == "Initial title"

    assert (
        await client.put(
            f"/api/v1/todos/{todo_id}",
            headers=headers,
            json={"title": "Updated title"},
        )
    ).status_code == 200
    list_after_update = await client.get("/api/v1/todos", headers=headers)
    assert list_after_update.json()["items"][0]["title"] == "Updated title"

    assert (
        await client.delete(f"/api/v1/todos/{todo_id}", headers=headers)
    ).status_code == 204
    assert (await client.get("/api/v1/todos", headers=headers)).json()["total"] == 0
