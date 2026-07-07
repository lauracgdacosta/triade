"""i18n mínimo: dicionário de traduções por locale, carregado de app/locales/*.json.

Escopo desta rodada: infraestrutura + telas de maior tráfego (base/topbar/
sidebar/dashboard). As demais páginas seguem com strings pt-BR fixas — ver
docs/roadmap.md.
"""

import json
from functools import lru_cache
from pathlib import Path

_LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
DEFAULT_LOCALE = "pt-BR"


@lru_cache
def _catalog(locale: str) -> dict[str, str]:
    path = _LOCALES_DIR / f"{locale}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def _default_catalog() -> dict[str, str]:
    return _catalog(DEFAULT_LOCALE)


def t(key: str, locale: str = DEFAULT_LOCALE) -> str:
    """Traduz `key` para `locale`; cai para o catálogo padrão e, por fim, para a própria key."""
    value = _catalog(locale).get(key)
    if value is not None:
        return value
    return _default_catalog().get(key, key)
