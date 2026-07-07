# Deploy

O backend é um serviço Docker padrão — funciona no Render (recomendado, usado
no `render.yaml` deste repositório) ou em qualquer plataforma que rode
containers (Fly.io, Railway, um VPS com `docker compose`, etc.).

## Por que Render (e não Vercel Functions)

O projeto escolhe um servidor Uvicorn persistente em vez de funções
serverless porque o Pomodoro/Agenda/Notificações dependem de estado de
processo, WebSockets/long-polling futuros e jobs em background — algo que
Vercel Functions (stateless, cold start) dificulta. Se preferir Vercel para o
front-end estático, o backend ainda pode rodar no Render e ser consumido via
`APP_ALLOWED_ORIGINS`/CORS.

## Deploy no Render

1. Crie um novo **Web Service** apontando para este repositório; o Render
   detecta o `render.yaml` automaticamente (Blueprint).
2. Preencha no painel do Render as variáveis marcadas `sync: false` no
   `render.yaml` (elas não têm valor padrão por segurança):
   `APP_BASE_URL`, `APP_ALLOWED_ORIGINS`, `DATABASE_URL`, `DATABASE_URL_SYNC`,
   `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`,
   `SUPABASE_JWT_SECRET`, `OAUTH_REDIRECT_URL`.
3. `APP_SECRET_KEY` é gerada automaticamente pelo Render
   (`generateValue: true`).
4. O healthcheck (`/healthz`) já está configurado no blueprint.

## Migrations em produção

Rode uma vez (shell do Render, ou como *Job* separado) antes do primeiro
deploy:

```bash
poetry run alembic upgrade head
```

Para deploys subsequentes com mudanças de schema, adicione um *pre-deploy
command* no Render executando o mesmo comando, ou rode manualmente antes de
promover a nova versão.

## Build local da imagem Docker

```bash
docker build -t triade .
docker run --env-file .env -p 8000:8000 triade
```

O `Dockerfile` é multi-stage: builda dependências com Poetry em uma camada e
copia apenas o necessário para a imagem final (`python:3.13-slim`, usuário
não-root, sem ferramentas de build).

## Verificando o Kanban colaborativo (Supabase Realtime)

O Kanban assina mudanças na tabela `tasks` via Supabase Realtime
(client-side, com a chave anônima — protegida por RLS, ver
`scripts/supabase_schema.sql`). Só funciona com `SUPABASE_URL`/
`SUPABASE_ANON_KEY` configurados (em SQLite local, sem Supabase, é um no-op
silencioso). No Supabase, confirme que a **Realtime** está habilitada para a
tabela `tasks` (Database → Replication). Para verificar: abra `/kanban` em
duas abas logadas no mesmo usuário, mova uma tarefa em uma delas — a outra
deve recarregar o quadro automaticamente em poucos segundos.

## Checklist antes de ir para produção

- [ ] `SESSION_COOKIE_SECURE=true` (cookies só em HTTPS).
- [ ] `APP_DEBUG=false` (desliga echo do SQLAlchemy e detalhes de erro).
- [ ] `APP_ALLOWED_ORIGINS` contém exatamente o(s) domínio(s) do front-end.
- [ ] Redirect URLs do Supabase Auth apontam para o domínio de produção.
- [ ] Bucket do Storage configurado (ver [Configuração](configuration.md)).
- [ ] `poetry run pytest` e `poetry run ruff check .` passando no CI antes do deploy.
