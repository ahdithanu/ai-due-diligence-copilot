import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.models import DeploymentModel
from backend.domain.schemas import DeploymentConfig

def get_default_growth_saas_config() -> DeploymentConfig:
    return DeploymentConfig(
        deployment_id="growth_saas_default",
        customer_name="Apex SaaS Capital",
        deployment_name="Growth Equity SaaS Standard",
        investment_strategy="growth_equity_saas",
        required_diligence_sections=[
            "financial_metrics",
            "unit_economics",
            "market_sizing",
            "competitive_analysis",
            "customer_retention",
            "product_roadmap"
        ],
        financial_thresholds={
            "min_gross_margin": 0.75,
            "max_cac_payback_months": 18.0,
            "min_nrr_pct": 110.0,
            "min_ebitda_margin_pct": -0.20,
            "max_leverage_ratio": 2.5
        },
        risk_thresholds={
            "max_customer_concentration_pct": "15%",
            "min_runway_months": "12"
        },
        required_evidence_types=[
            "audited_financials",
            "cap_table",
            "cohort_retention_data",
            "customer_contracts",
            "tech_stack_audit"
        ],
        evaluation_thresholds={
            "min_quality_score": 0.85,
            "max_iterations": 3.0
        },
        human_escalation_rules=[
            "gross_margin_below_threshold",
            "nrr_below_100",
            "critical_contradiction_detected",
            "high_customer_concentration"
        ],
        enabled_models=["gemini-2.5-pro", "gemini-2.5-flash"],
        model_roles={
            "synthesizer": "gemini-2.5-pro",
            "extractor": "gemini-2.5-flash",
            "evaluator": "gemini-2.5-pro"
        },
        allowed_tools=[
            "financial_calculator",
            "document_parser",
            "evidence_extractor",
            "benchmarking_service"
        ],
        output_requirements={
            "format": "ic_memo_pdf",
            "include_citations": True,
            "min_confidence_score": 0.8
        },
        custom_terminology={
            "ARR": "Annual Recurring Revenue",
            "NRR": "Net Retention Rate",
            "CAC": "Customer Acquisition Cost"
        }
    )

def get_default_traditional_buyout_config() -> DeploymentConfig:
    return DeploymentConfig(
        deployment_id="traditional_buyout_default",
        customer_name="Heritage Private Equity",
        deployment_name="Traditional LBO Standard",
        investment_strategy="traditional_buyout",
        required_diligence_sections=[
            "financial_history",
            "ebitda_adjustments",
            "working_capital",
            "capex_analysis",
            "debt_capacity",
            "management_assessment"
        ],
        financial_thresholds={
            "min_gross_margin": 0.40,
            "max_cac_payback_months": 24.0,
            "min_nrr_pct": 95.0,
            "min_ebitda_margin_pct": 0.15,
            "max_leverage_ratio": 4.5
        },
        risk_thresholds={
            "max_customer_concentration_pct": "25%",
            "min_runway_months": "6"
        },
        required_evidence_types=[
            "quality_of_earnings",
            "tax_returns",
            "debt_agreements",
            "asset_appraisals",
            "environmental_audit"
        ],
        evaluation_thresholds={
            "min_quality_score": 0.85,
            "max_iterations": 3.0
        },
        human_escalation_rules=[
            "negative_ebitda",
            "leverage_ratio_exceeded",
            "working_capital_deficit",
            "environmental_liability"
        ],
        enabled_models=["gemini-2.5-pro", "gemini-2.5-flash"],
        model_roles={
            "synthesizer": "gemini-2.5-pro",
            "extractor": "gemini-2.5-flash",
            "evaluator": "gemini-2.5-pro"
        },
        allowed_tools=[
            "financial_calculator",
            "document_parser",
            "evidence_extractor",
            "benchmarking_service"
        ],
        output_requirements={
            "format": "lbo_memo_pdf",
            "include_citations": True,
            "min_confidence_score": 0.85
        },
        custom_terminology={
            "EBITDA": "Earnings Before Interest, Taxes, Depreciation, and Amortization",
            "LBO": "Leveraged Buyout",
            "DSCR": "Debt Service Coverage Ratio"
        }
    )

async def create_deployment(db: AsyncSession, config: DeploymentConfig) -> DeploymentModel:
    db_dep = DeploymentModel(
        id=config.deployment_id,
        customer_name=config.customer_name,
        deployment_name=config.deployment_name,
        investment_strategy=config.investment_strategy,
        config_json=config.model_dump(mode="json")
    )
    db.add(db_dep)
    await db.commit()
    await db.refresh(db_dep)
    return db_dep

async def get_deployment(db: AsyncSession, deployment_id: str) -> Optional[DeploymentModel]:
    result = await db.execute(select(DeploymentModel).where(DeploymentModel.id == deployment_id))
    return result.scalar_one_or_none()

async def list_deployments(db: AsyncSession) -> List[DeploymentModel]:
    result = await db.execute(select(DeploymentModel).order_by(DeploymentModel.created_at.desc()))
    return list(result.scalars().all())

async def init_seed_deployments(db: AsyncSession):
    saas_config = get_default_growth_saas_config()
    existing_saas = await get_deployment(db, saas_config.deployment_id)
    if not existing_saas:
        await create_deployment(db, saas_config)

    buyout_config = get_default_traditional_buyout_config()
    existing_buyout = await get_deployment(db, buyout_config.deployment_id)
    if not existing_buyout:
        await create_deployment(db, buyout_config)
