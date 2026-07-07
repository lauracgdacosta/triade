# Diagrama Entidade-Relacionamento

Cobre **todas** as tabelas do schema (incluindo `notes` e `notifications`,
cuja UI chega na Rodada 2 — ver [Roadmap](roadmap.md)).

```mermaid
erDiagram
    USERS ||--o| USER_SETTINGS : has
    USERS ||--o{ ROLES : owns
    USERS ||--o{ CATEGORIES : owns
    USERS ||--o{ PROJECTS : owns
    USERS ||--o{ GOALS : owns
    USERS ||--o{ TAGS : owns
    USERS ||--o{ TASKS : owns
    USERS ||--o{ EVENTS : owns
    USERS ||--o{ KANBAN_BOARDS : owns
    USERS ||--o{ TIME_ENTRIES : owns
    USERS ||--o{ POMODORO_SESSIONS : owns
    USERS ||--o{ NOTES : owns
    USERS ||--o{ NOTIFICATIONS : owns

    PROJECTS ||--o{ GOALS : "grupo (opcional)"
    KANBAN_BOARDS ||--o{ KANBAN_COLUMNS : has

    CATEGORIES ||--o{ TASKS : categoriza
    PROJECTS ||--o{ TASKS : agrupa
    GOALS ||--o{ TASKS : rastreia
    ROLES ||--o{ TASKS : atribui
    KANBAN_COLUMNS ||--o{ TASKS : contém
    TASKS ||--o{ ATTACHMENTS : anexa
    TASKS }o--o{ TAGS : etiqueta

    TASKS ||--o{ TIME_ENTRIES : gera
    TASKS ||--o{ POMODORO_SESSIONS : cronometra
    CATEGORIES ||--o{ EVENTS : categoriza
    PROJECTS ||--o{ EVENTS : agrupa

    USERS {
        uuid id PK "= auth.users.id no Supabase"
        string email UK
        string display_name
        string avatar_url
        string timezone
        string locale
    }
    USER_SETTINGS {
        uuid user_id PK_FK
        enum theme
        string language
        bool time_format_24h
        bool week_start_monday
        int default_task_duration_minutes
        int pomodoro_work_minutes
        int pomodoro_break_minutes
    }
    ROLES {
        uuid id PK
        uuid user_id FK
        string name
        string color
        string icon
    }
    CATEGORIES {
        uuid id PK
        uuid user_id FK
        string name
        string icon
        string color
    }
    PROJECTS {
        uuid id PK
        uuid user_id FK
        string name
        text description
        string color
        date deadline
        numeric percent_complete
    }
    GOALS {
        uuid id PK
        uuid user_id FK
        uuid project_id FK "nullable"
        string title
        text description
        date deadline
        numeric percent_complete
    }
    TAGS {
        uuid id PK
        uuid user_id FK
        string name
        string color
    }
    TASKS {
        uuid id PK
        uuid user_id FK
        string title
        text description "HTML sanitizado"
        text notes
        date date
        time time
        int planned_duration_minutes
        int actual_duration_minutes
        enum priority "important|urgent|circumstantial|none"
        enum status "pending|in_progress|waiting|done|cancelled|archived"
        uuid category_id FK
        uuid project_id FK
        uuid goal_id FK
        uuid role_id FK
        uuid kanban_column_id FK
        int kanban_position
        string color
        string location
        datetime completed_at
    }
    ATTACHMENTS {
        uuid id PK
        uuid task_id FK
        string file_name
        string file_url "Supabase Storage"
        string mime_type
        int size_bytes
    }
    KANBAN_BOARDS {
        uuid id PK
        uuid user_id FK
        string name
        bool is_default
    }
    KANBAN_COLUMNS {
        uuid id PK
        uuid board_id FK
        string name
        string color
        int position
    }
    EVENTS {
        uuid id PK
        uuid user_id FK
        string title
        text description
        datetime start_at
        datetime end_at
        bool all_day
        string location
        string color
        string recurrence_rule "RFC5545 RRULE"
        uuid category_id FK
        uuid project_id FK
    }
    TIME_ENTRIES {
        uuid id PK
        uuid user_id FK
        uuid task_id FK "nullable"
        uuid project_id FK "nullable"
        uuid category_id FK "nullable"
        uuid role_id FK "nullable"
        datetime start_at
        datetime end_at
        int duration_minutes
        enum source "manual|pomodoro|timer"
    }
    POMODORO_SESSIONS {
        uuid id PK
        uuid user_id FK
        uuid task_id FK "nullable"
        enum mode "25_5|50_10|custom"
        int work_minutes
        int break_minutes
        int cycles_planned
        int cycles_completed
        enum status "running|paused|completed|cancelled"
        datetime started_at
        datetime ended_at
    }
    NOTES {
        uuid id PK
        uuid user_id FK
        string title
        text content_markdown
    }
    NOTIFICATIONS {
        uuid id PK
        uuid user_id FK
        enum type "task_due|event_reminder|goal_deadline|focus_time"
        string title
        text message
        bool read
        datetime scheduled_for
    }
```

## Convenções aplicadas

- Toda tabela de domínio tem `id` (UUID v4), `created_at`, `updated_at`.
- `ON DELETE CASCADE` do usuário para suas tabelas diretas; `ON DELETE SET
  NULL` nas referências opcionais de tarefa (categoria/projeto/meta/papel/
  coluna Kanban), para que remover uma categoria não apague as tarefas.
- Índices em toda FK e nas colunas usadas em filtros frequentes
  (`tasks.date`, `tasks.status`, `tasks.priority`, `events.start_at`/`end_at`).
