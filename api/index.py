"""Entrypoint que o Vercel detecta automaticamente (api/index.py com um `app` ASGI).

O código-fonte real vive em src/app/ (mesmo layout usado pelo Docker/Render,
com PYTHONPATH=/app/src) — aqui só ajustamos sys.path pra importar o mesmo
pacote sem duplicar nada.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from app.main import app  # noqa: F401
