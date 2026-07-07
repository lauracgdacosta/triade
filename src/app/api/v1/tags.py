"""Endpoints JSON de Etiquetas (Tags)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.user import User
from app.schemas.tag import TagCreate, TagRead
from app.services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagRead])
async def list_tags(user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)):
    return await TagService(db).list(user.id)


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(
    payload: TagCreate, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    return await TagService(db).create(user.id, payload)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = TagService(db)
    tag = await service.repo.get_for_user(tag_id, user.id)
    if tag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Etiqueta não encontrada.")
    await service.delete(tag)
