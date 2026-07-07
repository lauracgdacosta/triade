"""Renderização de páginas de erro."""

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.templating import templates


async def render_404(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "pages/404.html", {"request": request}, status_code=404
    )
