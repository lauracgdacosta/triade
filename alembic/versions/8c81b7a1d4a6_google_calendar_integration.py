"""google calendar integration

Revision ID: 8c81b7a1d4a6
Revises: d67b7ae36546
Create Date: 2026-07-08 18:18:57.844368

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8c81b7a1d4a6'
down_revision: str | None = 'd67b7ae36546'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "google_calendar_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("google_sub", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("calendar_id", sa.String(length=255), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scope", sa.String(length=255), nullable=False),
        sa.Column("sync_token", sa.Text(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "google_sub", name="uq_google_calendar_accounts_user_sub"),
    )
    op.create_index(
        op.f("ix_google_calendar_accounts_user_id"), "google_calendar_accounts", ["user_id"], unique=False
    )

    with op.batch_alter_table("events") as batch_op:
        batch_op.add_column(sa.Column("google_account_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("google_event_id", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("google_synced_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index(op.f("ix_events_google_account_id"), ["google_account_id"], unique=False)
        batch_op.create_index(op.f("ix_events_google_event_id"), ["google_event_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_events_google_account_id_google_calendar_accounts",
            "google_calendar_accounts",
            ["google_account_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("events") as batch_op:
        batch_op.drop_constraint("fk_events_google_account_id_google_calendar_accounts", type_="foreignkey")
        batch_op.drop_index(op.f("ix_events_google_event_id"))
        batch_op.drop_index(op.f("ix_events_google_account_id"))
        batch_op.drop_column("google_synced_at")
        batch_op.drop_column("google_event_id")
        batch_op.drop_column("google_account_id")

    op.drop_index(op.f("ix_google_calendar_accounts_user_id"), table_name="google_calendar_accounts")
    op.drop_table("google_calendar_accounts")
