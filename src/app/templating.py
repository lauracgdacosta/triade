"""Instância compartilhada do Jinja2Templates, com filtros/globals customizados."""

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from app.utils.datetime_utils import format_long_date, format_short_date
from app.utils.i18n import t

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.trim_blocks = True
templates.env.lstrip_blocks = True
templates.env.globals["t"] = t
templates.env.globals["format_long_date"] = format_long_date
templates.env.globals["format_short_date"] = format_short_date


def render(request: Request, name: str, context: dict, status_code: int = 200) -> HTMLResponse:
    """Renderiza o template e anexa o cookie de CSRF à resposta *efetivamente* enviada.

    Use esta função (em vez de `templates.TemplateResponse` diretamente) sempre que
    o contexto incluir `csrf_token`, para que o cookie correspondente seja setado.
    """
    response = templates.TemplateResponse(request, name, context, status_code=status_code)
    token = context.get("csrf_token")
    if token:
        from app.auth.csrf import attach_csrf_cookie

        attach_csrf_cookie(response, token)
    return response
