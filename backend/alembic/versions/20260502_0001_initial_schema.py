"""initial schema — users, projects, analysis_jobs, analysis_results

Revision ID: 20260502_0001
Revises:
Create Date: 2026-05-02 00:00:00

Phase 1 step 2 — creates the four core tables that anchor the platform:
- users
- projects (FK users.id)
- analysis_jobs (FK projects.id, users.id)
- analysis_results (FK analysis_jobs.id, UNIQUE for 1:1)

morphology_records and exports tables are added in a later migration during
Phase 2 step 12.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260502_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False, server_default="user"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name="fk_projects_owner_id_users", ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])

    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("input_path", sa.String(length=500), nullable=False),
        sa.Column(
            "parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(length=2000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"],
            name="fk_analysis_jobs_project_id_projects", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"],
            name="fk_analysis_jobs_owner_id_users", ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_analysis_jobs_project_id", "analysis_jobs", ["project_id"])
    op.create_index("ix_analysis_jobs_owner_id", "analysis_jobs", ["owner_id"])
    op.create_index("ix_analysis_jobs_status", "analysis_jobs", ["status"])
    op.create_index(
        "ix_analysis_jobs_owner_created",
        "analysis_jobs",
        ["owner_id", sa.text("created_at DESC")],
    )

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("cell_count", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("mask_path", sa.String(length=500), nullable=True),
        sa.Column("overlay_path", sa.String(length=500), nullable=True),
        sa.Column("density_path", sa.String(length=500), nullable=True),
        sa.Column("processing_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["analysis_jobs.id"],
            name="fk_analysis_results_job_id_jobs", ondelete="CASCADE",
        ),
        sa.UniqueConstraint("job_id", name="uq_analysis_results_job_id"),
    )
    op.create_index("ix_analysis_results_job_id", "analysis_results", ["job_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_analysis_results_job_id", table_name="analysis_results")
    op.drop_table("analysis_results")

    op.drop_index("ix_analysis_jobs_owner_created", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_status", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_owner_id", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_project_id", table_name="analysis_jobs")
    op.drop_table("analysis_jobs")

    op.drop_index("ix_projects_owner_id", table_name="projects")
    op.drop_table("projects")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
