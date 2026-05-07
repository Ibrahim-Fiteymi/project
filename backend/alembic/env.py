"""Alembic environment.

Reads the database URL from `Settings.database_url` (loaded from .env or env
vars) so there is one source of truth across the application and the
migration tool. Importing `backend.db.base` registers every SQLModel table
on `target_metadata`, which `alembic revision --autogenerate` then diffs.
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make project root importable so `backend.*` resolves.
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from backend.config import settings  # noqa: E402
from backend.db.base import metadata as target_metadata  # noqa: E402, F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

if not settings.database_url:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and set DATABASE_URL, "
        "or export it in the environment, before running Alembic."
    )

config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """Generate SQL without connecting to the database."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and apply migrations."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
