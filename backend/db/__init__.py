"""Database package — SQLModel engine, session factory, and ORM models.

Phase 1 step 2: foundation only. Models are defined and importable, the
engine is created when DATABASE_URL is configured, and Alembic migrations
own schema changes. No router or service wiring yet.
"""

from backend.db.base import Base, metadata  # noqa: F401
from backend.db.session import engine, get_session  # noqa: F401
