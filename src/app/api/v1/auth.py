"""Endpoints JSON de autenticação (signup/login/logout/forgot-password/refresh)."""

import contextlib

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.session import (
    clear_session_cookies,
    get_refresh_token,
    set_session_cookies,
)
from app.auth.supabase_client import SupabaseAuthError
from app.config import get_settings
from app.database import get_db
from app.schemas.auth import ForgotPasswordRequest, LoginRequest, SignUpRequest
from app.services.auth_service import AuthService
from app.utils.logging import audit
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/signup", status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_auth)
async def signup(request: Request, payload: SignUpRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    try:
        result = await service.sign_up(payload.email, payload.password)
    except SupabaseAuthError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    audit("signup", None, email=payload.email)
    return {
        "message": "Cadastro realizado. Verifique seu e-mail para confirmar a conta.",
        "confirmation_required": result.get("access_token") is None,
    }


@router.post("/login")
@limiter.limit(settings.rate_limit_auth)
async def login(request: Request, response: Response, payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    try:
        result = await service.sign_in(payload.email, payload.password)
    except SupabaseAuthError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc

    set_session_cookies(
        response, result["access_token"], result["refresh_token"], result.get("expires_in", 3600)
    )
    await service.sync_local_user_from_token(result["access_token"])
    audit("login", None, email=payload.email)
    return {"message": "Login realizado com sucesso."}


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    from app.auth.session import get_access_token

    access_token = get_access_token(request)
    if access_token:
        service = AuthService(db)
        await service.sign_out(access_token)
    clear_session_cookies(response)
    return {"message": "Logout realizado com sucesso."}


@router.post("/forgot-password")
@limiter.limit(settings.rate_limit_auth)
async def forgot_password(request: Request, payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    with contextlib.suppress(SupabaseAuthError):
        await service.forgot_password(payload.email)  # não revela se o e-mail existe ou não
    return {"message": "Se o e-mail existir, um link de redefinição foi enviado."}


@router.post("/refresh")
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    refresh_token = get_refresh_token(request)
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sem sessão para renovar.")
    service = AuthService(db)
    try:
        result = await service.refresh(refresh_token)
    except SupabaseAuthError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    set_session_cookies(
        response, result["access_token"], result["refresh_token"], result.get("expires_in", 3600)
    )
    return {"message": "Sessão renovada."}
