from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class AnalysisResult(SQLModel, table=True):
    __tablename__ = "analysis_results"

    id: Optional[int] = Field(default=None, primary_key=True)

    # One-to-one with AnalysisJob (enforced by UNIQUE).
    job_id: int = Field(foreign_key="analysis_jobs.id", unique=True, index=True)

    cell_count: int = Field(ge=0)
    mode: str = Field(max_length=32)  # "model" | "fallback-demo"

    # Storage keys (relative paths in dev local FS, S3 keys in prod). The DB
    # never stores binary content.
    mask_path: Optional[str] = Field(default=None, max_length=500)
    overlay_path: Optional[str] = Field(default=None, max_length=500)
    density_path: Optional[str] = Field(default=None, max_length=500)

    processing_ms: Optional[int] = Field(default=None, ge=0)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
