import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.tag import Tag
from app.models.todo import Todo
from app.models.user import User
from app.schemas.todo import (
    BulkStatusUpdate,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoUpdate,
)

router = APIRouter()
CACHE_TTL = 300
CACHE_KEY_PREFIX = "todos:list"


async def invalidate_todo_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    """Rotate a user's cache namespace after a committed todo mutation."""
    await redis.set(f"{CACHE_KEY_PREFIX}:{user_id}:version", str(uuid.uuid4()))


async def get_owned_todo(
    todo_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Todo:
    statement = (
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(Todo.id == todo_id, Todo.user_id == user_id)
    )
    todo = (await db.execute(statement)).scalar_one_or_none()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


def build_cache_key(user_id: uuid.UUID, version: str, filters: dict) -> str:
    serialized_filters = json.dumps(filters, sort_keys=True, separators=(",", ":"))
    return f"{CACHE_KEY_PREFIX}:{user_id}:{version}:{serialized_filters}"


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(
        None,
        alias="status",
        pattern="^(active|completed)$",
    ),
    tag_id: uuid.UUID | None = None,
    keyword: str | None = Query(None, max_length=200),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    filters = {
        "page": page,
        "size": size,
        "status": status_filter,
        "tag_id": str(tag_id) if tag_id else None,
        "keyword": keyword,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
    }
    version_key = f"{CACHE_KEY_PREFIX}:{current_user.id}:version"
    version = await redis.get(version_key) or "0"
    cache_key = build_cache_key(current_user.id, version, filters)

    cached = await redis.get(cache_key)
    if cached:
        return TodoListResponse(**json.loads(cached))

    predicates = [Todo.user_id == current_user.id]
    if status_filter:
        predicates.append(Todo.completed == (status_filter == "completed"))
    if keyword:
        predicates.append(Todo.title.ilike(f"%{keyword.strip()}%"))
    if date_from:
        predicates.append(Todo.created_at >= date_from)
    if date_to:
        predicates.append(Todo.created_at <= date_to)

    statement = select(Todo).where(*predicates)
    if tag_id:
        statement = statement.join(Todo.tags).where(
            Tag.id == tag_id,
            Tag.user_id == current_user.id,
        )

    total_statement = select(func.count()).select_from(statement.order_by(None).subquery())
    total = (await db.execute(total_statement)).scalar_one()
    paged_statement = (
        statement.options(selectinload(Todo.tags))
        .order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    todos = (await db.execute(paged_statement)).scalars().unique().all()

    response = TodoListResponse(
        items=[TodoResponse.model_validate(todo) for todo in todos],
        total=total,
        page=page,
        size=size,
    )
    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)
    return response


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(
    data: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = Todo(title=data.title, description=data.description, user_id=current_user.id)
    db.add(todo)
    await db.flush()
    await db.refresh(todo)
    await db.commit()
    await invalidate_todo_cache(redis, current_user.id)
    return todo


@router.patch("/bulk-status", response_model=list[TodoResponse])
async def bulk_status(
    data: BulkStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    statement = (
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(Todo.id.in_(data.todo_ids), Todo.user_id == current_user.id)
    )
    todos = (await db.execute(statement)).scalars().all()
    if len(todos) != len(set(data.todo_ids)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more todos were not found",
        )

    for todo in todos:
        todo.completed = data.completed
    await db.flush()
    await db.commit()
    await invalidate_todo_cache(redis, current_user.id)
    return todos


@router.post("/{todo_id}/tags/{tag_id}", response_model=TodoResponse)
async def attach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_owned_todo(todo_id, current_user.id, db)
    statement = select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id)
    tag = (await db.execute(statement)).scalar_one_or_none()
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    if tag not in todo.tags:
        todo.tags.append(tag)
        await db.flush()
        await db.commit()
        await invalidate_todo_cache(redis, current_user.id)
    return todo


@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_owned_todo(todo_id, current_user.id, db)
    tag = next((item for item in todo.tags if item.id == tag_id), None)
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag mapping not found",
        )

    todo.tags.remove(tag)
    await db.flush()
    await db.commit()
    await invalidate_todo_cache(redis, current_user.id)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_owned_todo(todo_id, current_user.id, db)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_id: uuid.UUID,
    data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_owned_todo(todo_id, current_user.id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(todo, field, value)

    await db.flush()
    await db.refresh(todo)
    await db.commit()
    await invalidate_todo_cache(redis, current_user.id)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_owned_todo(todo_id, current_user.id, db)
    await db.delete(todo)
    await db.flush()
    await db.commit()
    await invalidate_todo_cache(redis, current_user.id)
