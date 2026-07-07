"""Application factory (FastAPI)."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.utils.logging import configure_logging
from app.utils.rate_limit import limiter
from app.web.router import web_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Tríade — Gestão de Tempo, Agenda e Produtividade",
        description="API REST + páginas server-rendered (HTMX) para gestão de tempo, "
        "agenda, planejamento e produtividade.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SessionMiddleware, secret_key=settings.app_secret_key)

    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(web_router)

    @app.get("/healthz", tags=["health"])
    async def healthz() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    from app.auth.dependencies import AuthRedirectError

    @app.exception_handler(AuthRedirectError)
    async def auth_redirect_handler(request: Request, _exc: AuthRedirectError):
        next_url = request.url.path
        return RedirectResponse(url=f"/login?next={next_url}", status_code=status.HTTP_303_SEE_OTHER)

    @app.exception_handler(404)
    async def not_found(request: Request, _exc: Exception):
        from app.web.errors import render_404

        return await render_404(request)

    return app


app = create_app()
