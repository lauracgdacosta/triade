"""Páginas de autenticação: login, cadastro, esqueci senha, callback OAuth."""

from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.csrf import get_or_create_csrf_token, verify_csrf
from app.auth.dependencies import get_current_user_optional
from app.auth.session import (
    clear_session_cookies,
    get_access_token,
    set_session_cookies,
)
from app.auth.supabase_client import SupabaseAuthError
from app.database import get_db
from app.models.user import User
from app.schemas.auth import ForgotPasswordRequest, LoginRequest, SignUpRequest
from app.services.auth_service import AuthService
from app.templating import render

router = APIRouter(tags=["web-auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    next: str = "/dashboard",
    user: User | None = Depends(get_current_user_optional),
):
    if user:
        return RedirectResponse(next, status_code=status.HTTP_303_SEE_OTHER)
    csrf_token = get_or_create_csrf_token(request)
    return render(request, "pages/login.html", {"csrf_token": csrf_token, "next": next})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/dashboard"),
    csrf_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    try:
        payload = LoginRequest(email=email, password=password)
    except ValidationError:
        return render(
            request,
            "pages/login.html",
            {"csrf_token": csrf_token, "next": next, "error": "E-mail ou senha inválidos."},
            status_code=400,
        )

    service = AuthService(db)
    try:
        result = await service.sign_in(payload.email, payload.password)
    except SupabaseAuthError as exc:
        return render(
            request,
            "pages/login.html",
            {"csrf_token": csrf_token, "next": next, "error": exc.message},
            status_code=400,
        )

    redirect = RedirectResponse(next or "/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    set_session_cookies(
        redirect, result["access_token"], result["refresh_token"], result.get("expires_in", 3600)
    )
    await service.sync_local_user_from_token(result["access_token"])
    return redirect


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    csrf_token = get_or_create_csrf_token(request)
    return render(request, "pages/signup.html", {"csrf_token": csrf_token})


@router.post("/signup", response_class=HTMLResponse)
async def signup_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    display_name: str = Form(""),
    csrf_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    try:
        payload = SignUpRequest(email=email, password=password, display_name=display_name or None)
    except ValidationError as exc:
        return render(
            request,
            "pages/signup.html",
            {"csrf_token": csrf_token, "error": str(exc.errors()[0]["msg"])},
            status_code=400,
        )

    service = AuthService(db)
    try:
        await service.sign_up(payload.email, payload.password)
    except SupabaseAuthError as exc:
        return render(
            request, "pages/signup.html", {"csrf_token": csrf_token, "error": exc.message}, status_code=400
        )

    return render(
        request,
        "pages/signup.html",
        {"csrf_token": csrf_token, "success": "Cadastro realizado! Verifique seu e-mail para confirmar a conta."},
    )


@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    csrf_token = get_or_create_csrf_token(request)
    return render(request, "pages/forgot_password.html", {"csrf_token": csrf_token})


@router.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_submit(
    request: Request, email: str = Form(...), csrf_token: str = Form(...), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    try:
        payload = ForgotPasswordRequest(email=email)
        await AuthService(db).forgot_password(payload.email)
    except (ValidationError, SupabaseAuthError):
        pass
    return render(
        request,
        "pages/forgot_password.html",
        {"csrf_token": csrf_token, "success": "Se o e-mail existir, um link de redefinição foi enviado."},
    )


@router.get("/auth/oauth/{provider}")
async def oauth_start(provider: str, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return RedirectResponse(service.oauth_url(provider), status_code=status.HTTP_303_SEE_OTHER)


@router.get("/auth/callback", response_class=HTMLResponse)
async def oauth_callback_page(request: Request):
    """Página-ponte: lê o token do fragmento da URL (#access_token=...) via JS e
    o envia ao servidor, pois o fragmento nunca é enviado automaticamente ao backend."""
    return render(request, "pages/auth_callback.html", {})


@router.post("/auth/callback/session")
async def oauth_callback_session(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    access_token = body.get("access_token")
    refresh_token = body.get("refresh_token")
    if not access_token or not refresh_token:
        return {"ok": False}
    set_session_cookies(response, access_token, refresh_token, body.get("expires_in", 3600))
    await AuthService(db).sync_local_user_from_token(access_token)
    return {"ok": True}


@router.post("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    access_token = get_access_token(request)
    if access_token:
        await AuthService(db).sign_out(access_token)
    redirect = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    clear_session_cookies(redirect)
    return redirect
