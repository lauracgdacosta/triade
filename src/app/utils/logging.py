"""Configuração de logging estruturado (auditoria e observabilidade)."""

import logging
import sys

_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
    _CONFIGURED = True


audit_logger = logging.getLogger("app.audit")


def audit(action: str, user_id: str | None, **details: object) -> None:
    """Registra um evento de auditoria (ex.: login, criação/exclusão de recursos)."""
    audit_logger.info("action=%s user_id=%s details=%s", action, user_id, details)
