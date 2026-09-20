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
from app.schemas.todo import BulkStatusUpdate, TodoCreate, TodoListResponse, TodoResponse, TodoUpdate

router = APIRouter()
CACHE_TTL = 300


async def invalidate(redis: RedisClient, user_id: uuid.UUID) -> None:
    await redis.incr(f"todos:version:{user_id}")


async def owned_todo(todo_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Todo:
    stmt = select(Todo).options(selectinload(Todo.tags)).where(Todo.id == todo_id, Todo.user_id == user_id)
    todo = (await db.execute(stmt)).scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.get("", response_model=TodoListResponse)
async def list_todos(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), status_filter: str | None = Query(None, alias="status", pattern="^(active|completed)$"), tag_id: uuid.UUID | None = None, keyword: str | None = Query(None, max_length=200), date_from: datetime | None = None, date_to: datetime | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    filters = {"page": page, "size": size, "status": status_filter, "tag": str(tag_id) if tag_id else None, "keyword": keyword, "from": date_from.isoformat() if date_from else None, "to": date_to.isoformat() if date_to else None}
    version = await redis.get(f"todos:version:{current_user.id}") or "0"
    cache_key = f"todos:list:{current_user.id}:{version}:{json.dumps(filters, sort_keys=True, separators=(',', ':'))}"
    cached = await redis.get(cache_key)
    if cached:
        return TodoListResponse(**json.loads(cached))
    predicates = [Todo.user_id == current_user.id]
    if status_filter: predicates.append(Todo.completed == (status_filter == "completed"))
    if keyword: predicates.append(Todo.title.ilike(f"%{keyword.strip()}%"))
    if date_from: predicates.append(Todo.created_at >= date_from)
    if date_to: predicates.append(Todo.created_at <= date_to)
    query = select(Todo).where(*predicates)
    if tag_id: query = query.join(Todo.tags).where(Tag.id == tag_id, Tag.user_id == current_user.id)
    total = (await db.execute(select(func.count()).select_from(query.order_by(None).subquery()))).scalar_one()
    todos = (await db.execute(query.options(selectinload(Todo.tags)).order_by(Todo.created_at.desc(), Todo.id.desc()).offset((page - 1) * size).limit(size))).scalars().unique().all()
    response = TodoListResponse(items=[TodoResponse.model_validate(todo) for todo in todos], total=total, page=page, size=size)
    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)
    return response


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(data: TodoCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = Todo(title=data.title, description=data.description, user_id=current_user.id)
    db.add(todo); await db.flush(); await db.refresh(todo); await invalidate(redis, current_user.id)
    return todo


@router.patch("/bulk-status", response_model=list[TodoResponse])
async def bulk_status(data: BulkStatusUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todos = (await db.execute(select(Todo).options(selectinload(Todo.tags)).where(Todo.id.in_(data.todo_ids), Todo.user_id == current_user.id))).scalars().all()
    if len(todos) != len(set(data.todo_ids)):
        raise HTTPException(status_code=404, detail="One or more todos were not found")
    for todo in todos: todo.completed = data.completed
    await db.flush(); await invalidate(redis, current_user.id)
    return todos


@router.post("/{todo_id}/tags/{tag_id}", response_model=TodoResponse)
async def attach_tag(todo_id: uuid.UUID, tag_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await owned_todo(todo_id, current_user.id, db)
    tag = (await db.execute(select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id))).scalar_one_or_none()
    if not tag: raise HTTPException(status_code=404, detail="Tag not found")
    if tag not in todo.tags: todo.tags.append(tag)
    await db.flush(); await invalidate(redis, current_user.id)
    return todo


@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag(todo_id: uuid.UUID, tag_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await owned_todo(todo_id, current_user.id, db)
    tag = next((tag for tag in todo.tags if tag.id == tag_id), None)
    if not tag: raise HTTPException(status_code=404, detail="Tag mapping not found")
    todo.tags.remove(tag); await db.flush(); await invalidate(redis, current_user.id)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await owned_todo(todo_id, current_user.id, db)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(todo_id: uuid.UUID, data: TodoUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await owned_todo(todo_id, current_user.id, db)
    for key, value in data.model_dump(exclude_unset=True).items(): setattr(todo, key, value)
    await db.flush(); await db.refresh(todo); await invalidate(redis, current_user.id)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(todo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await owned_todo(todo_id, current_user.id, db)
    await db.delete(todo); await db.flush(); await invalidate(redis, current_user.id)
