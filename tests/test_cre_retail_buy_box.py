import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.services.deployment_service import (
    get_default_cre_retail_strip_config,
    init_seed_deployments,
    get_deployment,
    list_deployments
)
from backend.services.financial_calculator import (
    calculate_price_per_sf,
    calculate_cre_occupancy,
    calculate_tenant_concentration,
    calculate_restaurant_exposure,
    calculate_walt,
    calculate_parking_ratio
)
from backend.services.seed_service import init_seed_investments_if_empty
from backend.db.models import InvestmentModel, DeploymentModel
from sqlalchemy import select

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def test_cre_retail_strip_config_structure():
    """Verify CRE Small-Bay Retail Buy Box deployment configuration parameters."""
    config = get_default_cre_retail_strip_config()
    assert config.deployment_id == "cre_retail_strip_default"
    assert config.investment_strategy == "cre_retail_strip_center"
    assert "retail" in config.deployment_name.lower()
    
    thresholds = config.financial_thresholds
    assert thresholds["min_units"] == 5.0
    assert thresholds["max_units"] == 12.0
    assert thresholds["min_sf"] == 8000.0
    assert thresholds["max_sf"] == 25000.0
    assert thresholds["min_price"] == 1500000.0
    assert thresholds["max_price"] == 4000000.0
    assert thresholds["min_price_per_sf"] == 100.0
    assert thresholds["max_price_per_sf"] == 200.0
    assert thresholds["min_occupancy_pct"] == 80.0
    assert thresholds["min_walt_years"] == 3.0
    assert thresholds["max_single_tenant_concentration_pct"] == 30.0
    assert thresholds["max_restaurant_exposure_pct"] == 25.0
    assert thresholds["min_traffic_vpd"] == 15000.0
    assert thresholds["min_parking_ratio_per_1000_sf"] == 4.0

    assert config.risk_thresholds["min_vintage_year"] == "1985"
    assert "single_tenant_concentration_above_30_pct" in config.human_escalation_rules
    assert "restaurant_rent_roll_above_25_pct" in config.human_escalation_rules
    assert "occupancy_below_80_pct" in config.human_escalation_rules
    assert "vintage_prior_to_1985" in config.human_escalation_rules


def test_deterministic_cre_calculations():
    """Verify deterministic CRE formulas with 1.0 confidence."""
    # 1. Price per SF ($2.4M for 14,200 SF = $169.01/SF)
    metric_psf = calculate_price_per_sf(2400000.0, 14200.0, period="FY2024")
    assert metric_psf is not None
    assert metric_psf.metric_name == "Price_Per_SF"
    assert metric_psf.value == 169.01
    assert metric_psf.unit == "USD/SF"
    assert metric_psf.is_deterministic is True
    assert metric_psf.confidence == 1.0

    # 2. Occupancy rate (12,400 SF occupied / 14,200 SF total = 87.32%)
    metric_occ = calculate_cre_occupancy(12400.0, 14200.0, period="FY2024")
    assert metric_occ is not None
    assert metric_occ.metric_name == "Occupancy_Rate"
    assert metric_occ.value == 87.32
    assert metric_occ.unit == "percentage"

    # 3. Tenant Concentration ($58,800 top tenant / $240,000 total gross rent = 24.50%)
    metric_conc = calculate_tenant_concentration(58800.0, 240000.0, tenant_name="Oakridge Family Dental")
    assert metric_conc is not None
    assert metric_conc.value == 24.50
    assert metric_conc.unit == "percentage"

    # 4. Restaurant Exposure ($50,400 restaurant rent / $240,000 total = 21.00%)
    metric_rest = calculate_restaurant_exposure(50400.0, 240000.0)
    assert metric_rest is not None
    assert metric_rest.metric_name == "Restaurant_Exposure"
    assert metric_rest.value == 21.00
    assert metric_rest.unit == "percentage"

    # 5. WALT calculation: Sum(rent * years) / Sum(rent)
    leases = [
        {"rent": 58800.0, "years": 5.0},
        {"rent": 50400.0, "years": 3.0},
        {"rent": 37800.0, "years": 4.0},
        {"rent": 46200.0, "years": 3.5},
        {"rent": 33600.0, "years": 3.0},
        {"rent": 13200.0, "years": 2.0},
    ]
    metric_walt = calculate_walt(leases)
    assert metric_walt is not None
    assert metric_walt.metric_name == "WALT"
    assert metric_walt.value == 3.69
    assert metric_walt.unit == "years"

    # 6. Parking ratio (62 spaces for 14,200 SF = 4.37 stalls per 1,000 SF)
    metric_park = calculate_parking_ratio(62, 14200.0)
    assert metric_park is not None
    assert metric_park.metric_name == "Parking_Ratio"
    assert metric_park.value == 4.37
    assert metric_park.unit == "spaces_per_1000_sf"


def test_cre_buy_box_boundary_conditions():
    """Verify zero/invalid division guards for CRE calculations."""
    assert calculate_price_per_sf(2000000.0, 0.0) is None
    assert calculate_cre_occupancy(10000.0, 0.0) is None
    assert calculate_tenant_concentration(50000.0, 0.0) is None
    assert calculate_restaurant_exposure(30000.0, 0.0) is None
    assert calculate_walt([]) is None
    assert calculate_parking_ratio(50, 0.0) is None


@pytest.mark.asyncio
async def test_cre_deployment_and_seed_investments(async_db):
    """Verify CRE deployment is initialized and Oakridge Shoppes demo deal is seeded."""
    await init_seed_deployments(async_db)
    cre_dep = await get_deployment(async_db, "cre_retail_strip_default")
    assert cre_dep is not None
    assert cre_dep.investment_strategy == "cre_retail_strip_center"

    await init_seed_investments_if_empty(async_db)
    res = await async_db.execute(select(InvestmentModel).where(InvestmentModel.company_name == "Oakridge Shoppes"))
    oakridge = res.scalar_one_or_none()
    assert oakridge is not None
    assert oakridge.check_size_usd == 2400000.0
    assert "Small-Bay Retail" in oakridge.industry
    assert oakridge.state_snapshot_json["deployment_id"] == "cre_retail_strip_default"
