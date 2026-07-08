-- ============================================================================
-- Tríade — Schema completo (espelho SQL das migrations Alembic)
--
-- Como usar: cole este arquivo inteiro no SQL Editor do seu projeto Supabase
-- (https://app.supabase.com/project/_/sql/new) e execute. Ele cria todas as
-- tabelas da aplicação (Rodada 1 + tabelas já preparadas para a Rodada 2) e,
-- na segunda parte, integra a tabela `users` ao Supabase Auth (FK para
-- `auth.users`) e habilita Row Level Security em todas as tabelas.
--
-- Alternativa: ao invés de colar este SQL, você pode rodar
-- `poetry run alembic upgrade head` apontando DATABASE_URL para o Postgres do
-- Supabase — as migrations fazem exatamente o mesmo (menos a parte de RLS,
-- que é específica do Supabase e está apenas aqui).
-- ============================================================================

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 5b8c149e81d9

CREATE TABLE users (
    id UUID NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    display_name VARCHAR(150), 
    avatar_url VARCHAR(500), 
    timezone VARCHAR(50) NOT NULL, 
    locale VARCHAR(10) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE categories (
    user_id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    icon VARCHAR(50) NOT NULL, 
    color VARCHAR(20) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_categories_user_id ON categories (user_id);

CREATE TABLE kanban_boards (
    user_id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    is_default BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_kanban_boards_user_id ON kanban_boards (user_id);

CREATE TABLE notes (
    user_id UUID NOT NULL, 
    title VARCHAR(255), 
    content_markdown TEXT NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_notes_user_id ON notes (user_id);

CREATE TABLE notifications (
    user_id UUID NOT NULL, 
    type VARCHAR(30) NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    message TEXT, 
    read BOOLEAN NOT NULL, 
    scheduled_for TIMESTAMP WITHOUT TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_notifications_read ON notifications (read);

CREATE INDEX ix_notifications_user_id ON notifications (user_id);

CREATE TABLE projects (
    user_id UUID NOT NULL, 
    name VARCHAR(150) NOT NULL, 
    description TEXT, 
    color VARCHAR(20) NOT NULL, 
    deadline DATE, 
    percent_complete NUMERIC(5, 2) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_projects_user_id ON projects (user_id);

CREATE TABLE roles (
    user_id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    color VARCHAR(20) NOT NULL, 
    icon VARCHAR(50) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_roles_user_id ON roles (user_id);

CREATE TABLE tags (
    user_id UUID NOT NULL, 
    name VARCHAR(60) NOT NULL, 
    color VARCHAR(20) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_tags_user_id ON tags (user_id);

CREATE TABLE user_settings (
    user_id UUID NOT NULL, 
    theme VARCHAR(10) NOT NULL, 
    language VARCHAR(10) NOT NULL, 
    time_format_24h BOOLEAN NOT NULL, 
    week_start_monday BOOLEAN NOT NULL, 
    default_task_duration_minutes INTEGER NOT NULL, 
    pomodoro_work_minutes INTEGER NOT NULL, 
    pomodoro_break_minutes INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (user_id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE events (
    user_id UUID NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    description TEXT, 
    start_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    end_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    all_day BOOLEAN NOT NULL, 
    location VARCHAR(255), 
    color VARCHAR(20), 
    recurrence_rule VARCHAR(500), 
    category_id UUID, 
    project_id UUID, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL, 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE SET NULL, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_events_category_id ON events (category_id);

CREATE INDEX ix_events_end_at ON events (end_at);

CREATE INDEX ix_events_project_id ON events (project_id);

CREATE INDEX ix_events_start_at ON events (start_at);

CREATE INDEX ix_events_user_id ON events (user_id);

CREATE TABLE goals (
    user_id UUID NOT NULL, 
    project_id UUID, 
    title VARCHAR(150) NOT NULL, 
    description TEXT, 
    deadline DATE, 
    percent_complete NUMERIC(5, 2) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE SET NULL, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_goals_project_id ON goals (project_id);

CREATE INDEX ix_goals_user_id ON goals (user_id);

CREATE TABLE kanban_columns (
    board_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(20) NOT NULL,
    position INTEGER NOT NULL,
    maps_to_status VARCHAR(20),
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(board_id) REFERENCES kanban_boards (id) ON DELETE CASCADE
);

CREATE INDEX ix_kanban_columns_board_id ON kanban_columns (board_id);

CREATE TABLE tasks (
    user_id UUID NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    description TEXT, 
    notes TEXT, 
    date DATE, 
    time TIME WITHOUT TIME ZONE, 
    planned_duration_minutes INTEGER, 
    actual_duration_minutes INTEGER NOT NULL, 
    priority VARCHAR(20) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    category_id UUID, 
    project_id UUID, 
    goal_id UUID, 
    role_id UUID, 
    kanban_column_id UUID, 
    kanban_position INTEGER NOT NULL, 
    color VARCHAR(20), 
    location VARCHAR(255), 
    completed_at TIMESTAMP WITHOUT TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL, 
    FOREIGN KEY(goal_id) REFERENCES goals (id) ON DELETE SET NULL, 
    FOREIGN KEY(kanban_column_id) REFERENCES kanban_columns (id) ON DELETE SET NULL, 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE SET NULL, 
    FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE SET NULL, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_tasks_category_id ON tasks (category_id);

CREATE INDEX ix_tasks_date ON tasks (date);

CREATE INDEX ix_tasks_goal_id ON tasks (goal_id);

CREATE INDEX ix_tasks_kanban_column_id ON tasks (kanban_column_id);

CREATE INDEX ix_tasks_priority ON tasks (priority);

CREATE INDEX ix_tasks_project_id ON tasks (project_id);

CREATE INDEX ix_tasks_role_id ON tasks (role_id);

CREATE INDEX ix_tasks_status ON tasks (status);

CREATE INDEX ix_tasks_user_id ON tasks (user_id);

CREATE TABLE attachments (
    task_id UUID NOT NULL, 
    file_name VARCHAR(255) NOT NULL, 
    file_url VARCHAR(500) NOT NULL, 
    mime_type VARCHAR(100), 
    size_bytes INTEGER, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(task_id) REFERENCES tasks (id) ON DELETE CASCADE
);

CREATE INDEX ix_attachments_task_id ON attachments (task_id);

CREATE TABLE pomodoro_sessions (
    user_id UUID NOT NULL, 
    task_id UUID, 
    mode VARCHAR(20) NOT NULL, 
    work_minutes INTEGER NOT NULL, 
    break_minutes INTEGER NOT NULL, 
    cycles_planned INTEGER NOT NULL, 
    cycles_completed INTEGER NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    ended_at TIMESTAMP WITHOUT TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(task_id) REFERENCES tasks (id) ON DELETE SET NULL, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_pomodoro_sessions_task_id ON pomodoro_sessions (task_id);

CREATE INDEX ix_pomodoro_sessions_user_id ON pomodoro_sessions (user_id);

CREATE TABLE task_tags (
    task_id UUID NOT NULL, 
    tag_id UUID NOT NULL, 
    PRIMARY KEY (task_id, tag_id), 
    FOREIGN KEY(tag_id) REFERENCES tags (id) ON DELETE CASCADE, 
    FOREIGN KEY(task_id) REFERENCES tasks (id) ON DELETE CASCADE
);

CREATE TABLE time_entries (
    user_id UUID NOT NULL, 
    task_id UUID, 
    project_id UUID, 
    category_id UUID, 
    role_id UUID, 
    start_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    end_at TIMESTAMP WITHOUT TIME ZONE, 
    duration_minutes INTEGER NOT NULL, 
    source VARCHAR(20) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL, 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE SET NULL, 
    FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE SET NULL, 
    FOREIGN KEY(task_id) REFERENCES tasks (id) ON DELETE SET NULL, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_time_entries_category_id ON time_entries (category_id);

CREATE INDEX ix_time_entries_project_id ON time_entries (project_id);

CREATE INDEX ix_time_entries_role_id ON time_entries (role_id);

CREATE INDEX ix_time_entries_start_at ON time_entries (start_at);

CREATE INDEX ix_time_entries_task_id ON time_entries (task_id);

CREATE INDEX ix_time_entries_user_id ON time_entries (user_id);

INSERT INTO alembic_version (version_num) VALUES ('5b8c149e81d9') RETURNING alembic_version.version_num;

COMMIT;

-- ============================================================================
-- Parte 2 — Integração específica do Supabase (Auth + Row Level Security)
-- Requer o schema `auth` do Supabase; não roda em um Postgres genérico/local.
-- ============================================================================

BEGIN;

-- `public.users.id` É o mesmo UUID de `auth.users.id` (ver app/repositories/
-- user_repository.py: o perfil local é criado no primeiro login autenticado).
-- Esta FK garante exclusão em cascata quando o usuário é removido do Auth.
ALTER TABLE public.users
    ADD CONSTRAINT users_id_fkey FOREIGN KEY (id) REFERENCES auth.users (id) ON DELETE CASCADE;

-- Habilita RLS em todas as tabelas de dados do usuário.
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.task_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.kanban_boards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.kanban_columns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.time_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pomodoro_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- Tabelas com coluna `user_id` direta: usuário só enxerga/altera suas próprias linhas.
CREATE POLICY self_access ON public.users FOR ALL USING (id = auth.uid()) WITH CHECK (id = auth.uid());
CREATE POLICY self_access ON public.user_settings FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY self_access ON public.roles FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY self_access ON public.categories FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY self_access ON public.projects FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY self_access ON public.goals FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY self_access ON public.tags FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY self_access ON public.tasks FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY self_access ON public.kanban_boards FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY self_access ON public.events FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY self_access ON public.time_entries FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY self_access ON public.pomodoro_sessions FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY self_access ON public.notes FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY self_access ON public.notifications FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- Tabelas "filhas" (dono indireto via join com a tabela pai).
CREATE POLICY self_access ON public.kanban_columns FOR ALL USING (
    EXISTS (SELECT 1 FROM public.kanban_boards b WHERE b.id = kanban_columns.board_id AND b.user_id = auth.uid())
) WITH CHECK (
    EXISTS (SELECT 1 FROM public.kanban_boards b WHERE b.id = kanban_columns.board_id AND b.user_id = auth.uid())
);

CREATE POLICY self_access ON public.attachments FOR ALL USING (
    EXISTS (SELECT 1 FROM public.tasks t WHERE t.id = attachments.task_id AND t.user_id = auth.uid())
) WITH CHECK (
    EXISTS (SELECT 1 FROM public.tasks t WHERE t.id = attachments.task_id AND t.user_id = auth.uid())
);

CREATE POLICY self_access ON public.task_tags FOR ALL USING (
    EXISTS (SELECT 1 FROM public.tasks t WHERE t.id = task_tags.task_id AND t.user_id = auth.uid())
) WITH CHECK (
    EXISTS (SELECT 1 FROM public.tasks t WHERE t.id = task_tags.task_id AND t.user_id = auth.uid())
);

COMMIT;

