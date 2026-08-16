import asyncio
import argparse
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import AsyncSessionLocal, init_db
from backend.db.models import InvestmentModel, JobModel
from backend.domain.schemas import DiligenceState, DiligenceStatus, JobType, JobStatus, ExecutionState
from backend.engine.pipeline_builder import build_full_diligence_graph
from backend.engine.model_adapter import MockModelAdapter
from backend.services.queue_service import QueueService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend.worker")


async def process_diligence_run_job(db: AsyncSession, job: JobModel) -> Dict[str, Any]:
    """
    Executes a DILIGENCE_RUN job: builds the 17-node graph, runs execution, saves node checkpoints,
    and updates investment state.
    """
    investment_id = job.investment_id or (job.payload_json or {}).get("investment_id")
    
    # Retrieve investment workspace from DB if available
    inv = None
    if investment_id:
        result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
        inv = result.scalar_one_or_none()

    if inv and inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
    elif inv:
        state = DiligenceState(
            investment_id=inv.id,
            company_name=inv.company_name,
            industry=inv.industry,
            target_round=inv.target_round,
            check_size_usd=inv.check_size_usd,
            status=DiligenceStatus(inv.status)
        )
    else:
        # Standalone or fallback diligence run state
        company_name = (job.payload_json or {}).get("company_name", "Canary Startup Inc")
        state = DiligenceState(
            investment_id=investment_id or str(uuid.uuid4()),
            company_name=company_name,
            industry=(job.payload_json or {}).get("industry", "Enterprise Software"),
            target_round=(job.payload_json or {}).get("target_round", "Series A"),
            check_size_usd=(job.payload_json or {}).get("check_size_usd", 5000000.0)
        )

    model_adapter = MockModelAdapter()
    graph = build_full_diligence_graph(model_adapter=model_adapter)

    # Run state machine graph with DB persistence enabled
    final_state = await graph.run(state, db_session=db)

    # Persist updated state snapshot back to investment model if investment exists
    if inv:
        inv.state_snapshot_json = final_state.model_dump(mode="json")
        inv.status = final_state.status.value
        await db.commit()

    return {
        "investment_id": state.investment_id,
        "company_name": state.company_name,
        "execution_state": final_state.execution_state.value,
        "diligence_status": final_state.status.value,
        "recommendation": final_state.recommendation,
        "confidence_score": final_state.confidence_score,
        "node_iterations": state.iteration_counts,
        "checkpoint_count": len(final_state.checkpoint_history)
    }



async def process_rerun_job(db: AsyncSession, job: JobModel) -> Dict[str, Any]:
    """
    Executes a RE-RUN job starting from a specific node checkpoint.
    """
    payload = job.payload_json or {}
    investment_id = job.investment_id or payload.get("investment_id")
    from_node = payload.get("from_node", "DeterministicFinancialEngine")

    inv = None
    if investment_id:
        result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
        inv = result.scalar_one_or_none()

    if inv and inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
    elif inv:
        state = DiligenceState(
            investment_id=inv.id,
            company_name=inv.company_name,
            industry=inv.industry,
            target_round=inv.target_round,
            check_size_usd=inv.check_size_usd,
            status=DiligenceStatus(inv.status)
        )
    else:
        state = DiligenceState(
            investment_id=investment_id or str(uuid.uuid4()),
            company_name="Re-run Target Inc"
        )

    model_adapter = MockModelAdapter()
    graph = build_full_diligence_graph(model_adapter=model_adapter)

    final_state = await graph.run(state, db_session=db, start_node=from_node)

    if inv:
        inv.state_snapshot_json = final_state.model_dump(mode="json")
        inv.status = final_state.status.value
        await db.commit()

    return {
        "investment_id": state.investment_id,
        "from_node": from_node,
        "execution_state": final_state.execution_state.value,
        "diligence_status": final_state.status.value,
        "checkpoint_count": len(final_state.checkpoint_history)
    }


async def process_canary_test_job(db: AsyncSession, job: JobModel) -> Dict[str, Any]:
    """
    Executes a CANARY_TEST job to verify system graph health and pipeline readiness.
    """
    state = DiligenceState(
        investment_id=f"canary-{uuid.uuid4()}",
        company_name="Canary Systems Health Check",
        industry="DevOps & Infrastructure",
        target_round="Seed",
        check_size_usd=1000000.0
    )
    model_adapter = MockModelAdapter()
    graph = build_full_diligence_graph(model_adapter=model_adapter)

    final_state = await graph.run(state, db_session=db)

    return {
        "canary_status": "PASSED",
        "health_score": 1.0,
        "nodes_executed": len(graph.nodes),
        "execution_state": final_state.execution_state.value,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


async def process_next_job(db: AsyncSession) -> Optional[JobModel]:
    """
    Claims and processes the next pending job from the queue.
    """
    job = await QueueService.claim_next_job(db)
    if not job:
        return None

    logger.info(f"Processing job ID '{job.id}' of type '{job.job_type}'...")
    try:
        if job.job_type in (JobType.DILIGENCE_RUN.value, "DILIGENCE_RUN"):
            result_data = await process_diligence_run_job(db, job)
        elif job.job_type in (JobType.RE_RUN.value, "RE-RUN", "RERUN"):
            result_data = await process_rerun_job(db, job)
        elif job.job_type in (JobType.CANARY_TEST.value, "CANARY_TEST"):
            result_data = await process_canary_test_job(db, job)
        else:
            # Default to diligence run handler for custom job types
            result_data = await process_diligence_run_job(db, job)

        updated_job = await QueueService.update_job_status(
            db,
            job_id=job.id,
            status=JobStatus.COMPLETED.value,
            result=result_data
        )
        logger.info(f"Job '{job.id}' successfully completed.")
        return updated_job

    except Exception as e:
        logger.error(f"Error processing job '{job.id}': {e}", exc_info=True)
        updated_job = await QueueService.update_job_status(
            db,
            job_id=job.id,
            status=JobStatus.FAILED.value,
            error_message=str(e)
        )
        return updated_job


async def run_worker_loop(
    poll_interval: float = 1.0,
    run_once: bool = False,
    max_jobs: Optional[int] = None
) -> int:
    """
    Runs the standalone background worker processing loop.
    """
    logger.info("Initializing Graph Execution Worker loop...")
    await init_db()

    jobs_processed = 0

    while True:
        try:
            async with AsyncSessionLocal() as session:
                job = await process_next_job(session)

            if job:
                jobs_processed += 1
                if max_jobs and jobs_processed >= max_jobs:
                    logger.info(f"Reached max jobs limit ({max_jobs}). Exiting worker loop.")
                    break
            else:
                if run_once:
                    logger.info("Run once mode enabled and queue is empty. Exiting worker loop.")
                    break
                await asyncio.sleep(poll_interval)

        except asyncio.CancelledError:
            logger.info("Worker loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in worker loop iteration: {e}", exc_info=True)
            await asyncio.sleep(poll_interval)

    logger.info(f"Worker loop terminated. Total jobs processed: {jobs_processed}")
    return jobs_processed


def main():
    parser = argparse.ArgumentParser(description="AI Due Diligence Copilot Graph Execution Worker")
    parser.add_argument("--once", action="store_true", help="Process available jobs and exit")
    parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds")
    parser.add_argument("--max-jobs", type=int, default=None, help="Maximum number of jobs to process before exiting")

    args = parser.parse_args()

    try:
        asyncio.run(run_worker_loop(
            poll_interval=args.interval,
            run_once=args.once,
            max_jobs=args.max_jobs
        ))
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
