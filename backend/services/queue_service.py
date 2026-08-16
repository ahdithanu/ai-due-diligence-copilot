import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import JobModel
from backend.domain.schemas import JobType, JobStatus, JobRecord

logger = logging.getLogger(__name__)

VALID_JOB_TYPES = {JobType.DILIGENCE_RUN.value, JobType.RE_RUN.value, "RERUN", JobType.CANARY_TEST.value}
VALID_JOB_STATUSES = {
    JobStatus.QUEUED.value, JobStatus.PROCESSING.value,
    JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value
}

def _normalize_job_type(job_type: Union[str, JobType]) -> str:
    val = job_type.value if isinstance(job_type, JobType) else str(job_type)
    val_upper = val.upper()
    if val_upper in ("RE-RUN", "RERUN"):
        return JobType.RE_RUN.value
    elif val_upper == "DILIGENCE_RUN":
        return JobType.DILIGENCE_RUN.value
    elif val_upper == "CANARY_TEST":
        return JobType.CANARY_TEST.value
    else:
        # Fall back to provided string or DILIGENCE_RUN
        return val_upper if val_upper in VALID_JOB_TYPES else JobType.DILIGENCE_RUN.value

def _normalize_job_status(status: Union[str, JobStatus]) -> str:
    val = status.value if isinstance(status, JobStatus) else str(status)
    val_upper = val.upper()
    return val_upper if val_upper in VALID_JOB_STATUSES else JobStatus.QUEUED.value


class QueueService:
    """
    Async Job Queue Service managing asynchronous background task execution,
    status tracking, and execution metrics persistence.
    """

    @staticmethod
    async def enqueue_job(
        db: AsyncSession,
        job_type: Union[str, JobType],
        investment_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> JobModel:
        """
        Enqueues a new background execution job in the DB queue with status QUEUED.
        """
        norm_type = _normalize_job_type(job_type)
        now = datetime.now(timezone.utc)

        job = JobModel(
            id=str(uuid.uuid4()),
            investment_id=investment_id,
            job_type=norm_type,
            status=JobStatus.QUEUED.value,
            payload_json=payload or {},
            result_json=None,
            error_message=None,
            created_at=now,
            updated_at=now
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        logger.info(f"Enqueued job '{job.id}' of type '{norm_type}' for investment '{investment_id}'")
        return job

    @staticmethod
    async def get_job(db: AsyncSession, job_id: str) -> Optional[JobModel]:
        """
        Retrieves a job by its unique ID.
        """
        result = await db.execute(select(JobModel).where(JobModel.id == job_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_job_status(
        db: AsyncSession,
        job_id: str,
        status: Union[str, JobStatus],
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> JobModel:
        """
        Updates the status, output results, error details, and timestamps of a job.
        """
        norm_status = _normalize_job_status(status)
        now = datetime.now(timezone.utc)

        job = await QueueService.get_job(db, job_id)
        if not job:
            raise ValueError(f"Job with ID '{job_id}' not found.")

        job.status = norm_status
        job.updated_at = now

        if norm_status == JobStatus.PROCESSING.value and job.started_at is None:
            job.started_at = now

        if norm_status in (JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value):
            job.completed_at = now

        if result is not None:
            job.result_json = result

        if error_message is not None:
            job.error_message = error_message

        await db.commit()
        await db.refresh(job)
        logger.info(f"Updated job '{job_id}' status to '{norm_status}'")
        return job

    @staticmethod
    async def list_jobs(
        db: AsyncSession,
        investment_id: Optional[str] = None,
        status: Optional[Union[str, JobStatus]] = None,
        job_type: Optional[Union[str, JobType]] = None,
        limit: int = 50
    ) -> List[JobModel]:
        """
        Lists jobs with optional filtering by investment_id, status, or job_type.
        """
        stmt = select(JobModel).order_by(JobModel.created_at.desc())

        if investment_id:
            stmt = stmt.where(JobModel.investment_id == investment_id)
        if status:
            stmt = stmt.where(JobModel.status == _normalize_job_status(status))
        if job_type:
            stmt = stmt.where(JobModel.job_type == _normalize_job_type(job_type))

        stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def claim_next_job(db: AsyncSession) -> Optional[JobModel]:
        """
        Atomically claims the next pending QUEUED job by transitioning its status to PROCESSING.
        Returns the claimed JobModel or None if queue is empty.
        """
        stmt = select(JobModel).where(JobModel.status == JobStatus.QUEUED.value).order_by(JobModel.created_at.asc()).limit(1)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            return None

        now = datetime.now(timezone.utc)
        job.status = JobStatus.PROCESSING.value
        job.started_at = now
        job.updated_at = now

        await db.commit()
        await db.refresh(job)
        logger.info(f"Claimed job '{job.id}' ({job.job_type}) for processing.")
        return job


# Convenience module-level functions mapping directly to QueueService methods
async def enqueue_job(
    db: AsyncSession,
    job_type: Union[str, JobType],
    investment_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None
) -> JobModel:
    return await QueueService.enqueue_job(db, job_type=job_type, investment_id=investment_id, payload=payload)

async def get_job(db: AsyncSession, job_id: str) -> Optional[JobModel]:
    return await QueueService.get_job(db, job_id=job_id)

async def update_job_status(
    db: AsyncSession,
    job_id: str,
    status: Union[str, JobStatus],
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
) -> JobModel:
    return await QueueService.update_job_status(db, job_id=job_id, status=status, result=result, error_message=error_message)

async def list_jobs(
    db: AsyncSession,
    investment_id: Optional[str] = None,
    status: Optional[Union[str, JobStatus]] = None,
    job_type: Optional[Union[str, JobType]] = None,
    limit: int = 50
) -> List[JobModel]:
    return await QueueService.list_jobs(db, investment_id=investment_id, status=status, job_type=job_type, limit=limit)
