"""kanban column maps to status

Revision ID: d7933f8ac0ef
Revises: 5b8c149e81d9
Create Date: 2026-07-08 13:49:31.678962

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd7933f8ac0ef'
down_revision: str | None = '5b8c149e81d9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_DEFAULT_NAME_TO_STATUS = {
    "A Fazer": "pending",
    "Em Andamento": "in_progress",
    "Aguardando": "waiting",
    "Concluído": "done",
    "Arquivado": "archived",
}


def upgrade() -> None:
    op.add_column("kanban_columns", sa.Column("maps_to_status", sa.String(length=20), nullable=True))

    # Backfill de quadros já existentes: quem ainda tem os nomes de coluna
    # padrão (não renomeou) ganha o mapeamento automaticamente. Colunas
    # customizadas ficam com maps_to_status NULL e não participam da
    # sincronia bidirecional status<->kanban.
    kanban_columns = sa.table(
        "kanban_columns", sa.column("name", sa.String), sa.column("maps_to_status", sa.String)
    )
    for name, status in _DEFAULT_NAME_TO_STATUS.items():
        op.execute(
            kanban_columns.update().where(kanban_columns.c.name == name).values(maps_to_status=status)
        )


def downgrade() -> None:
    op.drop_column("kanban_columns", "maps_to_status")
