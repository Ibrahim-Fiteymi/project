from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class AnalysisJob(SQLModel, table=True):
    __tablename__ = "analysis_jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    status: str = Field(default=JobStatus.pending.value, max_length=16, index=True)
    input_path: str = Field(max_length=500)

    # Per-job inference parameters: threshold, min_area, image_size, mode, etc.
    parameters: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False, server_default="{}")
    )

    started_at: Optional[datetime] = Field(default=None, nullable=True)
    finished_at: Optional[datetime] = Field(default=None, nullable=True)
    error_message: Optional[str] = Field(default=None, nullable=True, max_length=2000)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
