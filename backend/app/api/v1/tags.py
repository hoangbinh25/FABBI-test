import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate

router = APIRouter()


async def invalidate_todos(redis: RedisClient, user_id: uuid.UUID) -> None:
    """Rotate this user's todo-list cache namespace after a tag mutation."""
    await redis.incr(f"todos:version:{user_id}")


async def owned_tag(tag_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Tag:
    statement = select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    tag = (await db.execute(statement)).scalar_one_or_none()
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return tag


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    statement = select(Tag).where(Tag.user_id == current_user.id).order_by(func.lower(Tag.name))
    return (await db.execute(statement)).scalars().all()


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    tag = Tag(user_id=current_user.id, name=data.name.strip(), color=data.color)
    db.add(tag)
    try:
        await db.flush()
    except IntegrityError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A tag with this name already exists") from error

    await invalidate_todos(redis, current_user.id)
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    tag = await owned_tag(tag_id, current_user.id, db)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tag, key, value.strip() if key == "name" else value)

    try:
        await db.flush()
    except IntegrityError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A tag with this name already exists") from error

    await invalidate_todos(redis, current_user.id)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    tag = await owned_tag(tag_id, current_user.id, db)
    await db.delete(tag)
    await db.flush()
    await invalidate_todos(redis, current_user.id)
