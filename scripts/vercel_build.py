"""Build step do Vercel: espelha src/app/static em public/static.

Vercel só serve arquivos estáticos que estejam em public/** via CDN (o
app.mount("/static", ...) do FastAPI é ignorado nesse ambiente) — então essa
cópia precisa rodar a cada deploy pra manter public/static em dia com o
static/ real que fica junto do código-fonte.
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
