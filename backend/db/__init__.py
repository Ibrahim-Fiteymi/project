"""Database package: engine, session, and bootstrap helpers.

Exports:
    engine, get_session — SQLAlchemy engine and FastAPI dependency.
    init_db()           — create tables (SQLite dev) and seed a default user/project.
    SYSTEM_USER_ID, DEFAULT_PROJECT_ID — fixed IDs used by the MVP until auth lands.
"""

from __future__ import annotations

import logging

from sqlmodel import Session, select

from backend.db.base import metadata
from backend.db.models import AnalysisJob, AnalysisResult, Project, User  # noqa: F401
from backend.db.session import engine, get_session

log = logging.getLogger(__name__)

SYSTEM_USER_ID = 1
DEFAULT_PROJECT_ID = 1

_SYSTEM_USER_EMAIL = "system@deeply.local"
_DEFAULT_PROJECT_NAME = "Default workspace"


def _seed_defaults(session: Session) -> None:
    """Create the system user and default project on first boot."""
    user = session.exec(select(User).where(User.email == _SYSTEM_USER_EMAIL)).first()
    if user is None:
        user = User(
            id=SYSTEM_USER_ID,
            email=_SYSTEM_USER_EMAIL,
            password_hash="!disabled",  # cannot be used to log in; auth lands in Phase 3
            role="admin",
        )
        session.add(user)
        session.flush()

    project = session.exec(
        select(Project).where(Project.id == DEFAULT_PROJECT_ID)
    ).first()
    if project is None:
        project = Project(
            id=DEFAULT_PROJECT_ID,
            owner_id=user.id or SYSTEM_USER_ID,
            name=_DEFAULT_PROJECT_NAME,
            description="Auto-created default workspace for unauthenticated MVP usage.",
        )
        session.add(project)

    session.commit()


def init_db() -> None:
    """Create tables and seed defaults. Idempotent."""
    metadata.create_all(engine)
    with Session(engine) as session:
        _seed_defaults(session)
    log.info("Database initialised at %s", engine.url)


__all__ = [
    "engine",
    "get_session",
    "init_db",
    "SYSTEM_USER_ID",
    "DEFAULT_PROJECT_ID",
]
