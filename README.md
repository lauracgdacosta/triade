# Tríade

Sistema de **Gestão de Tempo, Agenda, Planejamento e Produtividade** —
inspirado na experiência de ferramentas como Notion, ClickUp e TickTick, com
interface própria, construído com **FastAPI + HTMX + Supabase**.

> 📚 Documentação completa (instalação, configuração do Supabase,
> arquitetura, diagrama ER, referência de API, manual do usuário e roadmap):
> pasta [`docs/`](docs/index.md), servida via MkDocs Material
> (`poetry run mkdocs serve`).

## Funcionalidades

✅ **Entregue** — autenticação (Supabase Auth: e-mail/senha, confirmação por
e-mail, recuperação de senha, Google/GitHub OAuth) · Dashboard "Meu Dia" ·
Tarefas completas (prioridades, categorias, projetos, metas, papéis,
etiquetas, anexos, descrição rica, duplicar/arquivar/concluir/cancelar/
reabrir) · Agenda (dia/semana/mês, drag & drop, redimensionamento,
recorrência, conflito de horário) · Kanban (colunas customizáveis, Realtime
colaborativo) · Categorias, Projetos, Papéis e Metas (com progresso
calculado) · Cronômetro Pomodoro (25/5, 50/10, personalizado) com registro
automático de tempo · Relatórios (Chart.js: tempo por projeto/categoria/
papel/semana, eficiência) · Estatísticas avançadas (streak, taxa de
conclusão, atrasos) · Notificações (motor on-demand + central no topbar) ·
Busca global multi-entidade com filtros · Notas (Markdown, autosave) ·
Configurações (tema, idioma com i18n real, formato de hora/data, padrões de
Pomodoro) · Layout responsivo (desktop/tablet/celular) com sidebar
recolhível · CI (GitHub Actions).

Detalhes e próximos passos em [`docs/roadmap.md`](docs/roadmap.md).

## Stack

| Camada | Tecnologia |
|---|---|
| Front-end | HTML5, CSS3, JavaScript ES6+, Bootstrap 5, HTMX, Alpine.js, Font Awesome, Chart.js, Supabase Realtime |
| Back-end | Python 3.13+, FastAPI, Uvicorn, SQLAlchemy 2.0 (async), Pydantic v2, Alembic |
| Banco de dados | Supabase (PostgreSQL + Auth + Storage) |
| Testes / CI | Pytest, pytest-asyncio, pytest-cov (gate ≥70% de cobertura), GitHub Actions |
| Qualidade | Ruff, Clean Architecture, Repository Pattern, Service Layer, Dependency Injection |
| Deploy | Docker + Render (`render.yaml` incluso) |

Toda a interface é HTML renderizado pelo servidor (Jinja2 + HTMX) — não há
front-end em React/SPA.

## Início rápido

```bash
git clone <url-do-repositorio> triade
cd triade
poetry install
cp .env.example .env          # preencha com suas credenciais do Supabase
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --app-dir src
```

Acesse <http://localhost:8000>. Sem um `.env` preenchido, a aplicação roda
com SQLite local — suficiente para explorar a interface e rodar os testes.

Guia completo: [`docs/installation.md`](docs/installation.md) e
[`docs/configuration.md`](docs/configuration.md) (criação do projeto
Supabase, chaves, Storage, OAuth).

## Testes e qualidade

```bash
poetry run pytest              # cobertura ≥70% obrigatória (gate em pytest.ini)
poetry run ruff check .        # lint
poetry run ruff format .       # formatação
```

## Estrutura do projeto

```text
src/app/
  api/v1/        # API REST (JSON, documentada no Swagger em /docs)
  web/            # páginas server-rendered (HTMX + Jinja2)
  services/       # regra de negócio (Service Layer)
  repositories/   # acesso a dados (Repository Pattern, SQLAlchemy 2.0 async)
  models/         # ORM
  schemas/        # Pydantic (validação/serialização)
  auth/           # Supabase Auth, JWT, sessão, CSRF
  templates/      # Jinja2
  static/         # CSS / JS / imagens
  utils/          # paginação, datas, sanitização, logging
alembic/          # migrations
scripts/          # scripts/supabase_schema.sql (espelho SQL p/ o Supabase)
tests/            # unit/ + integration/
docs/             # MkDocs Material
```

Mais detalhes em [`docs/architecture.md`](docs/architecture.md).

## Deploy

```bash
docker build -t triade .
docker run --env-file .env -p 8000:8000 triade
```

Blueprint pronto para Render em [`render.yaml`](render.yaml). Passo a passo
completo em [`docs/deployment.md`](docs/deployment.md).

## Licença

Projeto de referência/estudo — ajuste a licença conforme a necessidade do seu
uso.
