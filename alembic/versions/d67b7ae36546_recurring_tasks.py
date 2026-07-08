"""recurring tasks

Revision ID: d67b7ae36546
Revises: d7933f8ac0ef
Create Date: 2026-07-08 17:12:38.458281

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd67b7ae36546'
down_revision: str | None = 'd7933f8ac0ef'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # batch_alter_table: no SQLite (usado localmente/testes), ALTER TABLE não
    # suporta adicionar constraints diretamente — o modo batch recria a
    # tabela por baixo dos panos. No Postgres (produção) vira um ALTER TABLE
    # normal.
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(
            sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.add_column(sa.Column("recurring_parent_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            op.f("ix_tasks_recurring_parent_id"), ["recurring_parent_id"], unique=False
        )
        batch_op.create_foreign_key(
            "fk_tasks_recurring_parent_id_tasks", "tasks", ["recurring_parent_id"], ["id"], ondelete="SET NULL"
        )


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_constraint("fk_tasks_recurring_parent_id_tasks", type_="foreignkey")
        batch_op.drop_index(op.f("ix_tasks_recurring_parent_id"))
        batch_op.drop_column("recurring_parent_id")
        batch_op.drop_column("is_recurring")
