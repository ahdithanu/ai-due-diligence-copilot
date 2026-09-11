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

from os import path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.services.seed_service import init_seed_investments_if_empty

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    await init_db()
    async with AsyncSessionLocal() as session:
        await init_seed_deployments(session)
        await init_seed_investments_if_empty(session)
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

# Mount frontend static assets if dist directory exists
frontend_dist = path.abspath(path.join(path.dirname(__file__), "..", "frontend", "dist"))
frontend_assets = path.join(frontend_dist, "assets")

if path.isdir(frontend_assets):
    app.mount("/assets", StaticFiles(directory=frontend_assets), name="assets")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.get("/")
async def root():
    index_file = path.join(frontend_dist, "index.html")
    if path.isfile(index_file):
        return FileResponse(index_file)
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

from fastapi import HTTPException

@app.get("/{full_path:path}")
async def catch_all_spa(full_path: str):
    # Only serve index.html for non-api routes if frontend/dist exists
    if full_path.startswith("api") or full_path.startswith("health") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    index_file = path.join(frontend_dist, "index.html")
    if path.isfile(index_file):
        return FileResponse(index_file)
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs"
    }
