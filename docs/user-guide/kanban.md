# Kanban

Em **/kanban**, cada usuário tem um quadro padrão criado automaticamente no
primeiro login, com as colunas **A Fazer**, **Em Andamento**, **Aguardando**,
**Concluído** e **Arquivado**.

- **Mover uma tarefa**: arraste o cartão para outra coluna. A posição é salva
  imediatamente.
- Tarefas aparecem no quadro assim que são associadas a uma coluna (isso
  acontece automaticamente ao movê-las pela primeira vez, ou pode ser feito
  via API).

As colunas podem ser criadas/renomeadas/removidas via API REST
(`/api/v1/kanban/columns`) — a tela de administração de colunas pela
interface web está prevista para uma próxima iteração.
