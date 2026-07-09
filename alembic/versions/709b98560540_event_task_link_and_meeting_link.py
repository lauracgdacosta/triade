"""event task link and meeting link

Revision ID: 709b98560540
Revises: 8c81b7a1d4a6
Create Date: 2026-07-09 18:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '709b98560540'
down_revision: str | None = '8c81b7a1d4a6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("events") as batch_op:
        batch_op.add_column(sa.Column("meeting_link", sa.String(length=500), nullable=True))

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("meeting_link", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("source_event_id", sa.Uuid(), nullable=True))
        batch_op.create_index(op.f("ix_tasks_source_event_id"), ["source_event_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_tasks_source_event_id_events", "events", ["source_event_id"], ["id"], ondelete="CASCADE"
        )


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_constraint("fk_tasks_source_event_id_events", type_="foreignkey")
        batch_op.drop_index(op.f("ix_tasks_source_event_id"))
        batch_op.drop_column("source_event_id")
        batch_op.drop_column("meeting_link")

    with op.batch_alter_table("events") as batch_op:
        batch_op.drop_column("meeting_link")
