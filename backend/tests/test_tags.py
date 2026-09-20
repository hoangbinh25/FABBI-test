import pytest
from httpx import AsyncClient


async def token(client: AsyncClient, email: str) -> str:
    response = await client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    return response.json()["access_token"]


def headers(value: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {value}"}


@pytest.mark.asyncio
async def test_tag_name_is_unique_case_insensitively(client: AsyncClient):
    auth = headers(await token(client, "tag-owner@example.com"))
    assert (await client.post("/api/v1/tags", json={"name": "Work"}, headers=auth)).status_code == 201
    assert (await client.post("/api/v1/tags", json={"name": "work"}, headers=auth)).status_code == 409


@pytest.mark.asyncio
async def test_cannot_attach_another_users_tag(client: AsyncClient):
    owner = headers(await token(client, "todo-owner@example.com"))
    other = headers(await token(client, "tag-owner-other@example.com"))
    todo = (await client.post("/api/v1/todos", json={"title": "Private"}, headers=owner)).json()
    tag = (await client.post("/api/v1/tags", json={"name": "Private tag"}, headers=other)).json()
    response = await client.post(f"/api/v1/todos/{todo['id']}/tags/{tag['id']}", headers=owner)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_bulk_update_rejects_another_users_todo(client: AsyncClient):
    owner = headers(await token(client, "bulk-owner@example.com"))
    other = headers(await token(client, "bulk-other@example.com"))
    own_todo = (await client.post("/api/v1/todos", json={"title": "Own"}, headers=owner)).json()
    other_todo = (await client.post("/api/v1/todos", json={"title": "Other"}, headers=other)).json()
    response = await client.patch("/api/v1/todos/bulk-status", json={"todo_ids": [own_todo["id"], other_todo["id"]], "completed": True}, headers=owner)
    assert response.status_code == 404
    unchanged = await client.get(f"/api/v1/todos/{own_todo['id']}", headers=owner)
    assert unchanged.json()["completed"] is False
