# Tríade

**Sistema de Gestão de Tempo, Agenda, Planejamento e Produtividade** — inspirado na
experiência de ferramentas como Notion, ClickUp e TickTick, com identidade visual
própria, construído com FastAPI + HTMX + Supabase.

## O que é

Tríade centraliza em um só lugar:

- **Dashboard "Meu Dia"** com saudação, progresso e indicadores de tempo.
- **Tarefas** completas: prioridades, categorias, projetos, metas, papéis,
  etiquetas, anexos, descrição rica.
- **Agenda** (dia/semana/mês) com arrastar-e-soltar, redimensionamento,
  recorrência e detecção de conflito de horário.
- **Kanban** com colunas customizáveis.
- **Projetos, Metas, Categorias e Papéis** com progresso calculado.
- **Cronômetro Pomodoro** (25/5, 50/10 ou personalizado) com registro automático
  de tempo.
- **Configurações** de tema (claro/escuro/automático), idioma, formato de hora e
  padrões de Pomodoro.

## Stack

| Camada | Tecnologia |
|---|---|
| Front-end | HTML5, CSS3, JavaScript ES6+, Bootstrap 5, HTMX, Alpine.js, Font Awesome |
| Back-end | Python 3.13+, FastAPI, Uvicorn, SQLAlchemy 2.0 (async), Pydantic v2, Alembic |
| Banco de dados | Supabase (PostgreSQL + Auth + Storage) |
| Testes | Pytest, pytest-asyncio, pytest-cov (gate ≥70%) |
| Qualidade | Ruff, Clean Architecture, Repository Pattern, Service Layer |
| Deploy | Render (Docker) — ver [Deploy](deployment.md) |

## Por onde começar

1. [Instalação](installation.md) — Poetry, pyenv, dependências.
2. [Configuração](configuration.md) — criar o projeto Supabase e preencher o `.env`.
3. [Arquitetura](architecture.md) — como as camadas se encaixam.
4. [Manual do usuário](user-guide/overview.md) — como usar cada tela.

!!! info "Escopo desta versão"
    Esta primeira entrega cobre o núcleo funcional completo (autenticação, Meu
    Dia, Tarefas, Agenda, Kanban, Categorias, Projetos, Papéis, Metas, Pomodoro
    e Configurações). O schema de banco já inclui as tabelas de Notas,
    Notificações e Relatórios — ver [Roadmap](roadmap.md) para o que vem a
    seguir.
