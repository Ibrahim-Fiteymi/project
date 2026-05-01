"""Pydantic response models for the MVP API."""

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
