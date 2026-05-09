"""auth: extend users + add refresh_tokens

Revision ID: 20260510_0002
Revises: 20260502_0001
Create Date: 2026-05-10 00:00:00

Phase 2 of the auth rollout. SQLite tests get the same shape from SQLModel
metadata via init_db(); this migration is what production Postgres runs.

- users: add is_active, last_login_at, failed_login_count
- refresh_tokens: new table, hashed token + user FK + expiry/revocation columns
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260510_0002"
down_revision: Union[str, None] = "20260502_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "failed_login_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_refresh_tokens_user_id_users", ondelete="CASCADE",
        ),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index(
        "ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_column("users", "failed_login_count")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "is_active")
