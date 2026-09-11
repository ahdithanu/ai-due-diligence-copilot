import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.main import app
from backend.db.database import AsyncSessionLocal
from backend.db.models import InvestmentModel
from backend.services.seed_service import init_seed_investments_if_empty

@pytest.mark.asyncio
async def test_auto_seed_investments_on_cold_start():
    async with AsyncSessionLocal() as session:
        await init_seed_investments_if_empty(session)
        res = await session.execute(select(func.count(InvestmentModel.id)))
        count = res.scalar_one_or_none()
        assert count is not None
        assert count >= 3

@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "AI Investment Due Diligence" in data["service"]

@pytest.mark.asyncio
async def test_root_and_spa_routing():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_root = await client.get("/")
        assert res_root.status_code == 200

        res_spa = await client.get("/workspaces")
        assert res_spa.status_code == 200

        res_api_404 = await client.get("/api/v1/nonexistent")
        assert res_api_404.status_code == 404
