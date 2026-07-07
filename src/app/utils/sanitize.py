"""Sanitização de HTML rico (descrição de tarefas) para prevenir XSS."""

import bleach

_ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s", "ul", "ol", "li", "a", "h1", "h2", "h3",
    "blockquote", "code", "pre", "span",
]
_ALLOWED_ATTRS = {"a": ["href", "title", "target", "rel"], "span": ["style"]}


def sanitize_html(raw_html: str | None) -> str | None:
    if raw_html is None:
        return None
    return bleach.clean(raw_html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True)
