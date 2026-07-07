# API REST

A API é gerada e documentada automaticamente pelo FastAPI:

- **Swagger UI**: `/docs`
- **Redoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

Todos os endpoints ficam sob o prefixo `/api/v1` e retornam/recebem JSON.
Autenticação é via cookie httpOnly (`triade_at`), definido pelo login — não é
necessário (nem suportado hoje) enviar um header `Authorization: Bearer`.

## Convenções

- **Autenticação obrigatória**: toda rota (exceto `/api/v1/auth/*` e
  `/healthz`) exige sessão válida; sem ela, retorna `401`.
- **Isolamento por usuário**: todo recurso pertence a um `user_id`; tentar
  acessar um recurso de outro usuário retorna `404` (não `403`, para não
  revelar a existência do recurso).
- **Verbos**: `GET` (listar/obter), `POST` (criar/ação), `PATCH` (atualizar
  parcialmente), `DELETE` (remover) — `204 No Content` em exclusões
  bem-sucedidas.
- **Erros de validação**: `422 Unprocessable Entity` (payload do Pydantic).
- **Rate limiting**: endpoints de autenticação são limitados por
  `RATE_LIMIT_AUTH` (padrão `10/minute`); os demais por `RATE_LIMIT_DEFAULT`
  (padrão `100/minute`).

## Grupos de endpoints

| Prefixo | Descrição |
|---|---|
| `/auth` | signup, login, logout, forgot-password, refresh |
| `/me` | perfil e preferências (`/me/settings`) do usuário autenticado |
| `/dashboard` | agregação do "Meu Dia" (`/dashboard/my-day`) |
| `/tasks` | CRUD + duplicar/arquivar/concluir/cancelar/reabrir/mover no Kanban/anexos |
| `/events` | CRUD da Agenda, com aviso de conflito de horário |
| `/kanban` | quadro padrão e colunas customizáveis |
| `/categories`, `/projects`, `/roles`, `/goals`, `/tags` | CRUD de organização |
| `/pomodoro` | iniciar sessão, concluir ciclo, cancelar |

## Exemplo: criar uma tarefa

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  --cookie "triade_at=<token>" \
  -d '{
        "title": "Revisar relatório mensal",
        "priority": "important",
        "date": "2026-03-10",
        "time": "14:30",
        "planned_duration_minutes": 45
      }'
```

## Exemplo: detectar conflito de horário na Agenda

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  --cookie "triade_at=<token>" \
  -d '{
        "title": "Reunião",
        "start_at": "2026-03-10T09:00:00",
        "end_at": "2026-03-10T10:00:00"
      }'
```

A resposta inclui `"has_conflict": true|false` — a criação **não é bloqueada**
por um conflito, apenas sinalizada, para que o usuário decida.
