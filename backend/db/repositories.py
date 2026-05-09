"""Repository helpers for analysis jobs and results.

Keeps SQL details out of the service layer. Every function takes an explicit
SQLModel ``Session`` so the caller controls transactions and testing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlmodel import Session, select

from backend.db import DEFAULT_PROJECT_ID, SYSTEM_USER_ID
from backend.db.models import AnalysisJob, AnalysisResult, JobStatus


def create_job(
    session: Session,
    *,
    job_uid: str,
    input_path: str,
    original_filename: Optional[str],
    parameters: dict[str, Any],
    project_id: int = DEFAULT_PROJECT_ID,
    owner_id: int = SYSTEM_USER_ID,
) -> AnalysisJob:
    job = AnalysisJob(
        job_uid=job_uid,
        project_id=project_id,
        owner_id=owner_id,
        status=JobStatus.processing.value,
        input_path=input_path,
        original_filename=original_filename,
        parameters=parameters,
        started_at=datetime.now(timezone.utc),
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def complete_job(
    session: Session,
    job: AnalysisJob,
    *,
    cell_count: int,
    mode: str,
    mask_path: Optional[str],
    overlay_path: Optional[str],
    processing_ms: int,
    density_path: Optional[str] = None,
) -> AnalysisResult:
    result = AnalysisResult(
        job_id=job.id,  # type: ignore[arg-type]
        cell_count=cell_count,
        mode=mode,
        mask_path=mask_path,
        overlay_path=overlay_path,
        density_path=density_path,
        processing_ms=processing_ms,
    )
    session.add(result)
    job.status = JobStatus.completed.value
    job.finished_at = datetime.now(timezone.utc)
    session.add(job)
    session.commit()
    session.refresh(result)
    return result


def fail_job(session: Session, job: AnalysisJob, message: str) -> None:
    job.status = JobStatus.failed.value
    job.error_message = message[:2000]
    job.finished_at = datetime.now(timezone.utc)
    session.add(job)
    session.commit()


def get_job_with_result(
    session: Session, job_uid: str
) -> Optional[tuple[AnalysisJob, Optional[AnalysisResult]]]:
    job = session.exec(select(AnalysisJob).where(AnalysisJob.job_uid == job_uid)).first()
    if job is None:
        return None
    result = session.exec(
        select(AnalysisResult).where(AnalysisResult.job_id == job.id)
    ).first()
    return job, result


def list_jobs(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    owner_id: Optional[int] = None,
) -> list[tuple[AnalysisJob, Optional[AnalysisResult]]]:
    # Single LEFT OUTER JOIN so we don't issue one extra SELECT per job.
    stmt = (
        select(AnalysisJob, AnalysisResult)
        .join(AnalysisResult, AnalysisResult.job_id == AnalysisJob.id, isouter=True)
    )
    if owner_id is not None:
        stmt = stmt.where(AnalysisJob.owner_id == owner_id)
    stmt = (
        stmt.order_by(AnalysisJob.created_at.desc())  # type: ignore[union-attr]
        .offset(offset)
        .limit(limit)
    )
    return [(job, result) for job, result in session.exec(stmt).all()]


def delete_job(session: Session, job_uid: str) -> bool:
    job = session.exec(select(AnalysisJob).where(AnalysisJob.job_uid == job_uid)).first()
    if job is None:
        return False
    result = session.exec(
        select(AnalysisResult).where(AnalysisResult.job_id == job.id)
    ).first()
    if result is not None:
        session.delete(result)
    session.delete(job)
    session.commit()
    return True
