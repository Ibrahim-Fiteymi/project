"""Shared SQLModel base and metadata.

Importing this module (and the models it loads) is enough to populate
SQLModel.metadata so Alembic autogenerate can see every table.
"""

from sqlmodel import SQLModel

# Importing the model modules registers each table on SQLModel.metadata.
# Order matters for foreign keys at table-creation time.
from backend.db.models.user import User  # noqa: F401, E402
from backend.db.models.project import Project  # noqa: F401, E402
from backend.db.models.analysis_job import AnalysisJob  # noqa: F401, E402
from backend.db.models.analysis_result import AnalysisResult  # noqa: F401, E402

Base = SQLModel
metadata = SQLModel.metadata
