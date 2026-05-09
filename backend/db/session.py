"""SQLAlchemy engine + SQLModel session factory.

Defaults to a local SQLite database under ``backend/storage/deeply.db`` so the
MVP runs without external services. In staging/production, set ``DATABASE_URL``
to a Postgres connection string and the same code path will use it.

The Alembic migrations target Postgres (JSONB). For SQLite the schema is
created from SQLModel metadata via ``init_db`` in ``backend/db/__init__.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from backend.config import settings


def _sqlite_default_url() -> str:
    db_path = Path(settings.storage_root) / "deeply.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # forward slashes are required by SQLAlchemy on Windows
    return f"sqlite:///{db_path.as_posix()}"


def _build_engine() -> Engine:
    url = settings.database_url or _sqlite_default_url()
    connect_args: dict = {}
    if url.startswith("sqlite"):
        # Allow the engine to be shared across FastAPI worker threads.
        connect_args["check_same_thread"] = False
    return create_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        future=True,
        connect_args=connect_args,
    )


# Module-level singleton, eagerly built so init_db can use it on startup.
engine: Engine = _build_engine()


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a SQLModel session."""
    with Session(engine) as session:
        yield session
