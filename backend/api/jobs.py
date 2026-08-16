from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from backend.db.database import get_db
from backend.domain.schemas import JobType, JobStatus, JobRecord
from backend.services.queue_service import QueueService

router = APIRouter(prefix="/jobs", tags=["Queue Service & Jobs"])


class EnqueueJobRequest(BaseModel):
    job_type: str = Field(default="DILIGENCE_RUN", description="Job type: DILIGENCE_RUN, RE-RUN, CANARY_TEST")
    investment_id: Optional[str] = Field(default=None, description="Optional target investment ID")
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Job execution parameters")


@router.post("/enqueue", response_model=JobRecord, status_code=status.HTTP_201_CREATED)
async def enqueue_job_endpoint(
    req: EnqueueJobRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Enqueues a new background execution job into the async queue.
    """
    job_model = await QueueService.enqueue_job(
        db,
        job_type=req.job_type,
        investment_id=req.investment_id,
        payload=req.payload
    )
    return JobRecord(
        id=job_model.id,
        investment_id=job_model.investment_id,
        job_type=job_model.job_type,
        status=job_model.status,
        payload=job_model.payload_json or {},
        result=job_model.result_json,
        error_message=job_model.error_message,
        created_at=job_model.created_at,
        updated_at=job_model.updated_at,
        started_at=job_model.started_at,
        completed_at=job_model.completed_at
    )


@router.get("/{job_id}", response_model=JobRecord)
async def get_job_endpoint(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the status and result details of a queued or processed job by ID.
    """
    job_model = await QueueService.get_job(db, job_id)
    if not job_model:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found.")

    return JobRecord(
        id=job_model.id,
        investment_id=job_model.investment_id,
        job_type=job_model.job_type,
        status=job_model.status,
        payload=job_model.payload_json or {},
        result=job_model.result_json,
        error_message=job_model.error_message,
        created_at=job_model.created_at,
        updated_at=job_model.updated_at,
        started_at=job_model.started_at,
        completed_at=job_model.completed_at
    )


@router.get("", response_model=List[JobRecord])
async def list_jobs_endpoint(
    investment_id: Optional[str] = Query(None, description="Filter by investment ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED)"),
    job_type_filter: Optional[str] = Query(None, alias="job_type", description="Filter by job type (DILIGENCE_RUN, RE-RUN, CANARY_TEST)"),
    limit: int = Query(50, ge=1, le=200, description="Max jobs to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists jobs with optional filtering by investment_id, status, or job_type.
    """
    jobs = await QueueService.list_jobs(
        db,
        investment_id=investment_id,
        status=status_filter,
        job_type=job_type_filter,
        limit=limit
    )
    return [
        JobRecord(
            id=j.id,
            investment_id=j.investment_id,
            job_type=j.job_type,
            status=j.status,
            payload=j.payload_json or {},
            result=j.result_json,
            error_message=j.error_message,
            created_at=j.created_at,
            updated_at=j.updated_at,
            started_at=j.started_at,
            completed_at=j.completed_at
        )
        for j in jobs
    ]


@router.post("/canary", response_model=JobRecord, status_code=status.HTTP_201_CREATED)
async def trigger_canary_test(
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers a CANARY_TEST job to verify queue worker pipeline execution readiness.
    """
    job_model = await QueueService.enqueue_job(
        db,
        job_type=JobType.CANARY_TEST.value,
        payload={"trigger": "api_healthcheck"}
    )
    return JobRecord(
        id=job_model.id,
        investment_id=job_model.investment_id,
        job_type=job_model.job_type,
        status=job_model.status,
        payload=job_model.payload_json or {},
        result=job_model.result_json,
        error_message=job_model.error_message,
        created_at=job_model.created_at,
        updated_at=job_model.updated_at,
        started_at=job_model.started_at,
        completed_at=job_model.completed_at
    )
