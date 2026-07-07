# Instalação

## Pré-requisitos

- **Python 3.13+** — recomendado via [pyenv](https://github.com/pyenv-win/pyenv-win) (Windows) ou [pyenv](https://github.com/pyenv/pyenv) (Linux/Mac).
- **Poetry 2.x** — `pipx install poetry` ou veja [python-poetry.org](https://python-poetry.org/docs/#installation).
- **Git**.
- Uma conta [Supabase](https://supabase.com) (gratuita) — ver [Configuração](configuration.md).

## Passo a passo

```bash
git clone <url-do-repositorio> triade
cd triade

# Fixa a versão do Python via pyenv (opcional, mas recomendado)
pyenv install 3.13.0
pyenv local 3.13.0

# Cria o virtualenv e instala as dependências (main + dev)
poetry install

# Copia o template de variáveis de ambiente
cp .env.example .env
```

Edite o `.env` com as credenciais do seu projeto Supabase (veja
[Configuração](configuration.md)). Enquanto isso não for feito, a aplicação
roda localmente com SQLite (`sqlite+aiosqlite:///./triade.db`), útil para
explorar a interface e rodar os testes sem depender de rede.

## Rodando as migrations

```bash
poetry run alembic upgrade head
```

Isso cria todas as tabelas no banco apontado por `DATABASE_URL`. Para aplicar
diretamente no Supabase, veja [Configuração](configuration.md#schema-sql).

## Subindo o servidor

```bash
poetry run uvicorn app.main:app --reload --app-dir src
```

Acesse:

- Aplicação: <http://localhost:8000>
- Swagger UI (API REST): <http://localhost:8000/docs>
- Redoc: <http://localhost:8000/redoc>

## Rodando os testes

```bash
poetry run pytest
```

O `pytest.ini` já aplica cobertura mínima de 70% (`--cov-fail-under=70`) contra
um banco SQLite em memória — não requer Supabase configurado.

## Lint

```bash
poetry run ruff check .
poetry run ruff format .
```

## Docker (opcional)

```bash
docker compose up --build
```

Sobe a aplicação em `http://localhost:8000` lendo variáveis do `.env`. Um
serviço Postgres local opcional está disponível via
`docker compose --profile local-db up`, útil apenas para desenvolvimento
offline (a persistência real do projeto é sempre o Supabase).

## Documentação (MkDocs)

```bash
poetry run mkdocs serve
```

Abre a documentação em <http://localhost:8001> com recarregamento automático.
