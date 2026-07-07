"""Endpoints JSON de Papéis (Roles)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.user import User
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleRead])
async def list_roles(user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)):
    return await RoleService(db).list(user.id)


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    return await RoleService(db).create(user.id, payload)


@router.patch("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: uuid.UUID,
    payload: RoleUpdate,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = RoleService(db)
    role = await service.get(role_id, user.id)
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Papel não encontrado.")
    return await service.update(role, payload)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = RoleService(db)
    role = await service.get(role_id, user.id)
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Papel não encontrado.")
    await service.delete(role)
