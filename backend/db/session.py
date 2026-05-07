"""SQLAlchemy engine + SQLModel session factory.

Engine is created lazily and only if Settings.database_url is set, so the
existing MVP keeps running when no database is configured. Routers obtain
a session via the `get_session` FastAPI dependency.
"""

from __future__ import annotations

from typing import Iterator, Optional

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from backend.config import settings


def _build_engine() -> Optional[Engine]:
    if not settings.database_url:
        return None
    return create_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        future=True,
    )


# Module-level singleton; None when DATABASE_URL is not configured.
engine: Optional[Engine] = _build_engine()


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a SQLModel session.

    Raises RuntimeError when DATABASE_URL is not configured. Callers that
    must function without a database should not depend on this function.
    """
    if engine is None:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it in .env or the environment."
        )
    with Session(engine) as session:
        yield session
