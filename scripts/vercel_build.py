"""Espelha src/app/static em public/static para o deploy no Vercel.

Vercel só serve arquivos estáticos que estejam em public/** via CDN (o
app.mount("/static", ...) do FastAPI é ignorado nesse ambiente). O
pyproject.toml fica fora do bundle enviado ao Vercel (ver .vercelignore,
necessário porque é formato Poetry e o uv exige uma tabela [project]), então
o hook [tool.vercel.scripts] não roda automaticamente no build — rode este
script manualmente e comite public/static sempre que src/app/static mudar.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_STATIC = ROOT / "src" / "app" / "static"
PUBLIC_STATIC = ROOT / "public" / "static"


def main() -> None:
    if PUBLIC_STATIC.exists():
        shutil.rmtree(PUBLIC_STATIC)
    shutil.copytree(SRC_STATIC, PUBLIC_STATIC)
    print(f"Copiado {SRC_STATIC} -> {PUBLIC_STATIC}")


if __name__ == "__main__":
    main()
