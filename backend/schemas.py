"""Pydantic response models for the MVP API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    device: str
    model_loaded: bool
    mode: str = Field(description='"model" | "fallback-demo" | "uninitialised"')
    load_error: Optional[str] = None


class AnalysisMetadata(BaseModel):
    original_filename: str
    mode: str
    threshold: Optional[float] = None
    min_area: int
    image_size: int
    processing_ms: int
    device: str


class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    message: str
    cell_count: int
    input_url: str
    mask_url: str
    overlay_url: str
    metadata: AnalysisMetadata


class AnalysisHistoryItem(BaseModel):
    """Compact summary of a persisted analysis for the history list."""

    job_id: str
    status: str
    cell_count: Optional[int] = None
    original_filename: Optional[str] = None
    mode: Optional[str] = None
    processing_ms: Optional[int] = None
    input_url: Optional[str] = None
    mask_url: Optional[str] = None
    overlay_url: Optional[str] = None
    threshold: Optional[float] = None
    min_area: Optional[int] = None
    created_at: datetime
    finished_at: Optional[datetime] = None


class AnalysisHistoryResponse(BaseModel):
    items: list[AnalysisHistoryItem]
    total: int
