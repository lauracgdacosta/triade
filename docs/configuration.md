# Configuração

## 1. Criar o projeto no Supabase

1. Acesse [app.supabase.com](https://app.supabase.com) e crie um novo projeto.
2. Anote a **URL do projeto** e as chaves em *Project Settings → API*:
   - `anon` `public` key → `SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY` (secreta — nunca exponha no front-end)
3. Em *Project Settings → API → JWT Settings*, copie o **JWT Secret** →
   `SUPABASE_JWT_SECRET`.
4. Em *Project Settings → Database*, copie a connection string e monte:
   - `DATABASE_URL` (usada pela aplicação): troque o driver para `postgresql+asyncpg://...`
   - `DATABASE_URL_SYNC` (opcional, outras ferramentas): `postgresql+psycopg2://...`

## 2. Schema do banco {#schema-sql}

Duas formas equivalentes de aplicar o schema:

=== "Via Alembic (recomendado)"

    ```bash
    poetry run alembic upgrade head
    ```

    Usa `DATABASE_URL` do `.env` e cria todas as tabelas + índices.

=== "Via SQL Editor do Supabase"

    Cole o conteúdo de [`scripts/supabase_schema.sql`](https://github.com)
    (arquivo no repositório) no SQL Editor do projeto. Ele contém, em duas
    partes:

    1. O DDL completo (todas as tabelas, índices e FKs) — idêntico ao gerado
       pelo Alembic.
    2. Integração específica do Supabase: FK de `users.id` para
       `auth.users.id`, e políticas de **Row Level Security (RLS)** que
       restringem cada tabela ao próprio dono (`auth.uid()`).

    A parte 2 só funciona dentro do Supabase (depende do schema `auth`), por
    isso não faz parte da migration Alembic genérica.

!!! note "Sobre RLS e a conexão da aplicação"
    A aplicação conecta-se ao Postgres usando a connection string do banco
    (não via PostgREST), então as políticas de RLS não afetam as consultas do
    backend — a autorização por usuário já é garantida na camada de serviço
    (todo repositório filtra por `user_id`). O RLS é uma camada extra de
    defesa caso outra ferramenta (Supabase Studio, Realtime, PostgREST) acesse
    o banco diretamente.

## 3. Storage (anexos de tarefas)

1. Em *Storage*, crie um bucket chamado **attachments** (ou o nome definido em
   `SUPABASE_STORAGE_BUCKET`).
2. Marque o bucket como público (leitura) se quiser links diretos, ou privado
   se preferir servir os anexos por trás de autenticação — a implementação
   atual usa a service role key no backend e URLs públicas do bucket.

## 4. Authentication

1. Em *Authentication → Providers*, habilite **Email** (com confirmação por
   e-mail) e, se desejar, **Google** e **GitHub**.
2. Em *Authentication → URL Configuration*, defina:
   - **Site URL**: `http://localhost:8000` (produção: sua URL do Render)
   - **Redirect URLs**: adicione `http://localhost:8000/auth/callback` (e o
     equivalente em produção).
3. Para OAuth (Google/GitHub), siga o guia do Supabase para cadastrar as
   credenciais de cada provedor e colá-las na tela do provider correspondente.

## 5. Variáveis de ambiente

Todas as variáveis estão documentadas em [`.env.example`](https://github.com).
Resumo:

| Variável | Descrição |
|---|---|
| `APP_SECRET_KEY` | Chave usada pelo `SessionMiddleware`. Gere com `openssl rand -hex 32`. |
| `APP_BASE_URL` / `APP_ALLOWED_ORIGINS` | URL pública e origens permitidas (CORS). |
| `DATABASE_URL` | Connection string async (`postgresql+asyncpg://...` em produção). |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` | Credenciais do projeto Supabase. |
| `SUPABASE_STORAGE_BUCKET` | Nome do bucket de anexos. |
| `OAUTH_REDIRECT_URL` | Deve bater com o cadastrado no Supabase Auth. |
| `SESSION_COOKIE_SECURE` | `true` em produção (HTTPS obrigatório para cookies). |
| `RATE_LIMIT_DEFAULT` / `RATE_LIMIT_AUTH` | Limites do `slowapi` (ex.: `100/minute`). |

## 6. Configurações do usuário dentro do app

Depois de logado, cada usuário ajusta suas próprias preferências em
**Configurações**: tema, idioma, formato de hora, primeiro dia da semana,
duração padrão de tarefa e valores padrão do Pomodoro — tudo persistido na
tabela `user_settings`.
