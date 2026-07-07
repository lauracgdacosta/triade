"""Endpoints JSON de Metas."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalRead, GoalUpdate
from app.services.goal_service import GoalService

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=list[GoalRead])
async def list_goals(user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)):
    return await GoalService(db).list(user.id)


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: GoalCreate, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = GoalService(db)
    goal = await service.create(user.id, payload)
    return await service.get_read(goal.id, user.id)


@router.get("/{goal_id}", response_model=GoalRead)
async def get_goal(
    goal_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    goal = await GoalService(db).get_read(goal_id, user.id)
    if goal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Meta não encontrada.")
    return goal


@router.patch("/{goal_id}", response_model=GoalRead)
async def update_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdate,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = GoalService(db)
    goal = await service.get(goal_id, user.id)
    if goal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Meta não encontrada.")
    await service.update(goal, payload)
    return await service.get_read(goal_id, user.id)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = GoalService(db)
    goal = await service.get(goal_id, user.id)
    if goal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Meta não encontrada.")
    await service.delete(goal)
