import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from backend.db.database import Base
from backend.db.models import InvestmentModel, JobModel, GraphCheckpointModel
from backend.domain.schemas import JobType, JobStatus, DiligenceStatus
from backend.services.queue_service import QueueService, enqueue_job, get_job, update_job_status, list_jobs
from backend.worker import process_next_job, run_worker_loop
from backend.main import app


@pytest_asyncio.fixture
async def async_db():
    """In-memory SQLite database session for unit tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_enqueue_and_get_job(async_db: AsyncSession):
    # Enqueue DILIGENCE_RUN
    job1 = await QueueService.enqueue_job(
        async_db,
        job_type=JobType.DILIGENCE_RUN,
        investment_id="inv-123",
        payload={"company_name": "Test Co"}
    )
    assert job1.id is not None
    assert job1.job_type == JobType.DILIGENCE_RUN.value
    assert job1.status == JobStatus.QUEUED.value
    assert job1.investment_id == "inv-123"

    # Get Job
    fetched = await QueueService.get_job(async_db, job1.id)
    assert fetched is not None
    assert fetched.id == job1.id
    assert fetched.payload_json == {"company_name": "Test Co"}


@pytest.mark.asyncio
async def test_update_job_status(async_db: AsyncSession):
    job = await QueueService.enqueue_job(
        async_db,
        job_type=JobType.CANARY_TEST,
        payload={"test": True}
    )
    assert job.status == JobStatus.QUEUED.value

    # Update to PROCESSING
    updated_proc = await QueueService.update_job_status(
        async_db,
        job_id=job.id,
        status=JobStatus.PROCESSING
    )
    assert updated_proc.status == JobStatus.PROCESSING.value
    assert updated_proc.started_at is not None

    # Update to COMPLETED
    result_dict = {"health": "OK", "score": 1.0}
    updated_comp = await QueueService.update_job_status(
        async_db,
        job_id=job.id,
        status=JobStatus.COMPLETED,
        result=result_dict
    )
    assert updated_comp.status == JobStatus.COMPLETED.value
    assert updated_comp.completed_at is not None
    assert updated_comp.result_json == result_dict


@pytest.mark.asyncio
async def test_list_jobs(async_db: AsyncSession):
    j1 = await QueueService.enqueue_job(async_db, job_type=JobType.DILIGENCE_RUN, investment_id="inv-A")
    j2 = await QueueService.enqueue_job(async_db, job_type=JobType.RE_RUN, investment_id="inv-A")
    j3 = await QueueService.enqueue_job(async_db, job_type=JobType.CANARY_TEST, investment_id="inv-B")

    # List all
    all_jobs = await QueueService.list_jobs(async_db)
    assert len(all_jobs) >= 3

    # Filter by investment_id
    inv_a_jobs = await QueueService.list_jobs(async_db, investment_id="inv-A")
    assert len(inv_a_jobs) == 2

    # Filter by job_type
    canary_jobs = await QueueService.list_jobs(async_db, job_type=JobType.CANARY_TEST)
    assert len(canary_jobs) == 1
    assert canary_jobs[0].id == j3.id


@pytest.mark.asyncio
async def test_worker_canary_test_job(async_db: AsyncSession):
    job = await QueueService.enqueue_job(async_db, job_type=JobType.CANARY_TEST)
    assert job.status == JobStatus.QUEUED.value

    processed = await process_next_job(async_db)
    assert processed is not None
    assert processed.id == job.id
    assert processed.status == JobStatus.COMPLETED.value
    assert processed.result_json is not None
    assert processed.result_json.get("canary_status") == "PASSED"


@pytest.mark.asyncio
async def test_worker_diligence_run_job(async_db: AsyncSession):
    inv = InvestmentModel(
        id="inv-test-diligence",
        company_name="Apex Quantum AI",
        industry="Artificial Intelligence",
        target_round="Series A",
        check_size_usd=5000000.0,
        status=DiligenceStatus.CREATED.value
    )
    async_db.add(inv)
    await async_db.commit()

    job = await QueueService.enqueue_job(
        async_db,
        job_type=JobType.DILIGENCE_RUN,
        investment_id=inv.id
    )

    processed = await process_next_job(async_db)
    assert processed is not None
    assert processed.id == job.id
    assert processed.status == JobStatus.COMPLETED.value
    assert processed.result_json.get("investment_id") == inv.id
    assert processed.result_json.get("diligence_status") is not None

    # Check updated investment model in DB
    refreshed_inv = await async_db.get(InvestmentModel, inv.id)
    assert refreshed_inv.state_snapshot_json is not None


@pytest.mark.asyncio
async def test_worker_rerun_job(async_db: AsyncSession):
    inv = InvestmentModel(
        id="inv-rerun-test",
        company_name="Rerun Analytics Inc",
        industry="SaaS",
        target_round="Seed",
        check_size_usd=2000000.0,
        status=DiligenceStatus.CREATED.value
    )
    async_db.add(inv)
    await async_db.commit()

    job = await QueueService.enqueue_job(
        async_db,
        job_type=JobType.RE_RUN,
        investment_id=inv.id,
        payload={"from_node": "FinancialAnalyst"}
    )

    processed = await process_next_job(async_db)
    assert processed is not None
    assert processed.status == JobStatus.COMPLETED.value
    assert processed.result_json.get("from_node") == "FinancialAnalyst"


@pytest.mark.asyncio
async def test_jobs_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Enqueue via API
        resp = await client.post("/api/v1/jobs/enqueue", json={
            "job_type": "DILIGENCE_RUN",
            "payload": {"company_name": "API Startup"}
        })
        assert resp.status_code == 201
        data = resp.json()
        job_id = data["id"]
        assert data["job_type"] == "DILIGENCE_RUN"
        assert data["status"] == "QUEUED"

        # Get Job via API
        resp_get = await client.get(f"/api/v1/jobs/{job_id}")
        assert resp_get.status_code == 200
        assert resp_get.json()["id"] == job_id

        # List Jobs via API
        resp_list = await client.get("/api/v1/jobs")
        assert resp_list.status_code == 200
        assert len(resp_list.json()) >= 1

        # Trigger Canary via API
        resp_canary = await client.post("/api/v1/jobs/canary")
        assert resp_canary.status_code == 201
        assert resp_canary.json()["job_type"] == "CANARY_TEST"
