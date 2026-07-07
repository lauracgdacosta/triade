# Roadmap

## Rodada 1 — entregue

Auth (Supabase) · Dashboard "Meu Dia" · Tarefas completas · Agenda (dia/
semana/mês, drag&drop, recorrência, conflito) · Kanban · Categorias ·
Projetos · Papéis · Metas · Pomodoro · Configurações básicas · Layout
responsivo com dark/light/auto.

## Rodada 2 — entregue

- **Relatórios** (`/reports`): dashboards com Chart.js — tempo por projeto/
  categoria/papel/semana (agregado de `time_entries`), eficiência
  (planejado × realizado), tempo médio por tarefa.
- **Estatísticas avançadas**: dias consecutivos produtivos (streak), taxa de
  conclusão, tempo perdido (tarefas canceladas), tarefas atrasadas — na
  mesma página de Relatórios.
- **Notificações**: motor on-demand (gerado a cada carregamento do topbar,
  idempotente) para tarefas vencidas, compromissos próximos e metas com
  prazo perto, com central no topbar.
- **Busca global** (`/search`): busca multi-entidade (tarefas, projetos,
  metas, eventos) com filtros por data/categoria/projeto/papel/prioridade/
  status.
- **Notas**: painel lateral em Markdown com autosave, acessível pelo ícone no
  topbar.
- **Configurações avançadas**: i18n real (pt-BR/en-US/es-ES) nas telas de
  maior tráfego (navegação, topbar, Meu Dia) e localização de formato de
  data — demais páginas seguem em pt-BR fixo como próximo passo.
- **Supabase Realtime**: Kanban colaborativo — assina mudanças em `tasks` e
  recarrega o quadro automaticamente (no-op sem Supabase configurado).
- **CI**: GitHub Actions (`.github/workflows/ci.yml`) rodando `ruff check` +
  `pytest` (gate de cobertura ≥70%) em cada PR/push para `main`.

## Rodada 3 — ideias futuras

- Tradução completa de todas as páginas (hoje só as de maior tráfego).
- Lançamento manual de `time_entries` pela UI (hoje só via Pomodoro).
- Notificações por push/e-mail, além da central in-app.
- Busca com ranking/relevância em vez de correspondência textual simples.
