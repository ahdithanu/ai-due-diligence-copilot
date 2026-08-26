from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.db.database import init_db, AsyncSessionLocal
from backend.services.deployment_service import init_seed_deployments
from backend.api.investments import router as investments_router
from backend.api.diligence import router as diligence_router
from backend.api.deployments import router as deployments_router
from backend.api.failure_lab import router as failure_lab_router
from backend.api.jobs import router as jobs_router
from backend.api.operations import router as operations_router
from backend.api.demo import router as demo_router
from backend.api.institutional import router as institutional_router
from backend.api.rag import router as rag_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    await init_db()
    async with AsyncSessionLocal() as session:
        await init_seed_deployments(session)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(investments_router, prefix=settings.API_V1_STR)
app.include_router(diligence_router, prefix=settings.API_V1_STR)
app.include_router(deployments_router, prefix=settings.API_V1_STR)
app.include_router(failure_lab_router, prefix=settings.API_V1_STR)
app.include_router(jobs_router, prefix=settings.API_V1_STR)
app.include_router(operations_router, prefix=settings.API_V1_STR)
app.include_router(demo_router, prefix=settings.API_V1_STR)
app.include_router(institutional_router, prefix=settings.API_V1_STR)
app.include_router(rag_router, prefix=settings.API_V1_STR)





@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
