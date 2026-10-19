from typing import List
from backend.domain.schemas import (
    FundingRoundHistory,
    MarketCompetitorIntel,
    ExecutiveProfile,
    OrganizationalHealthMetrics,
    ExternalIntelligenceResponse,
)

DEFAULT_FUNDING_HISTORY: List[FundingRoundHistory] = [
    FundingRoundHistory(
        round_name="Pre-Seed Round",
        date="2021-06-15",
        amount_raised_usd=750_000.0,
        post_money_valuation_usd=4_000_000.0,
        lead_investors=["Y Combinator", "Angel Syndicate"],
        dilution_pct=18.75,
    ),
    FundingRoundHistory(
        round_name="Series Seed",
        date="2022-10-01",
        amount_raised_usd=3_000_000.0,
        post_money_valuation_usd=16_000_000.0,
        lead_investors=["Founders Fund Syndicate", "SV Angels"],
        dilution_pct=18.75,
    ),
    FundingRoundHistory(
        round_name="Series A (Target Round)",
        date="2024-03-20",
        amount_raised_usd=10_000_000.0,
        post_money_valuation_usd=50_000_000.0,
        lead_investors=["Apex SaaS Capital (Proposed Lead)"],
        dilution_pct=20.00,
    ),
]

DEFAULT_COMPETITORS: List[MarketCompetitorIntel] = [
    MarketCompetitorIntel(
        name="NexusAI Platform",
        headquarters="San Francisco, CA",
        total_raised_usd=45_000_000.0,
        last_round="Series B ($30M)",
        estimated_arr_usd=14_500_000.0,
        growth_momentum="HIGH",
        key_differentiator="Focuses on heavy legacy ERP migrations; higher ACV ($120k) but 9-month sales cycle.",
    ),
    MarketCompetitorIntel(
        name="CogniFlow Enterprise",
        headquarters="New York, NY",
        total_raised_usd=28_000_000.0,
        last_round="Series A ($18M)",
        estimated_arr_usd=9_200_000.0,
        growth_momentum="MODERATE",
        key_differentiator="Strong UI and front-office integrations; lacks backend zero-retention DLP security.",
    ),
    MarketCompetitorIntel(
        name="AgentCraft Systems",
        headquarters="Austin, TX",
        total_raised_usd=18_500_000.0,
        last_round="Series A ($12M)",
        estimated_arr_usd=6_000_000.0,
        growth_momentum="STEADY",
        key_differentiator="Open-source distribution wedge; slower enterprise monetization and higher churn.",
    ),
]

DEFAULT_EXECUTIVES: List[ExecutiveProfile] = [
    ExecutiveProfile(
        name="Elena Rostova",
        title="Chief Executive Officer & Co-Founder",
        tenure_years=4.2,
        prior_pedigree="Ex-Stripe VP Product, Stanford CS '16",
        equity_ownership_pct=24.5,
        flight_risk_level="LOW",
        status_notes="Visionary product leader; highly committed with strong Board alignment.",
    ),
    ExecutiveProfile(
        name="Dr. Marcus Vance",
        title="Chief Technology Officer & Co-Founder",
        tenure_years=4.2,
        prior_pedigree="Ex-Google Brain AI Research, MIT PhD '17",
        equity_ownership_pct=19.5,
        flight_risk_level="MEDIUM",
        status_notes="Architectural genius & sole committer on core IP; requires VP Eng succession buffer.",
    ),
    ExecutiveProfile(
        name="Sarah Jenkins",
        title="VP of Engineering",
        tenure_years=1.8,
        prior_pedigree="Ex-Datadog Director of Infrastructure",
        equity_ownership_pct=2.5,
        flight_risk_level="LOW",
        status_notes="Scaled engineering org from 15 to 55 devs; robust operational rigor.",
    ),
    ExecutiveProfile(
        name="David Sterling",
        title="Interim Head of Sales (Director)",
        tenure_years=0.8,
        prior_pedigree="Ex-Snowflake Regional Director",
        equity_ownership_pct=0.8,
        flight_risk_level="HIGH",
        status_notes="Interim coverage following CRO departure 4 months ago; permanent VP Sales search underway.",
    ),
]

DEFAULT_ORG_HEALTH = OrganizationalHealthMetrics(
    glassdoor_rating=4.4,
    headcount_total=115,
    yoy_headcount_growth_pct=38.5,
    annual_regretted_attrition_pct=7.2,
    engineering_velocity_score=91.4,
    retention_health="Top Decile (Industry Benchmark: 14.5% Attrition)",
)


class ExternalIntelligenceService:
    """Provides market intelligence, competitor funding signals, executive team audit, and org health analytics."""

    def get_external_intel(
        self, investment_id: str, company_name: str = "Acme SaaS AI"
    ) -> ExternalIntelligenceResponse:
        return ExternalIntelligenceResponse(
            investment_id=investment_id,
            company_name=company_name,
            funding_history=DEFAULT_FUNDING_HISTORY,
            competitors=DEFAULT_COMPETITORS,
            executive_team=DEFAULT_EXECUTIVES,
            org_health=DEFAULT_ORG_HEALTH,
            data_source="PitchBook, Crunchbase & LinkedIn Enterprise Radar",
        )


external_intelligence_service = ExternalIntelligenceService()
