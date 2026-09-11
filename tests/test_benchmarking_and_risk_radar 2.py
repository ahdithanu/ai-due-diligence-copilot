import pytest
import uuid
from typing import List

from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    FinancialMetricRecord,
    ClaimNode,
    ContradictionRecord,
    SpecialistAnalysis,
    MaterialityLevel,
    ClaimType,
    RedFlagSeverity,
    PortfolioComparisonResponse,
    RedFlagAlert
)
from backend.services.benchmarking_service import (
    generate_portfolio_comparison,
    detect_portfolio_red_flags,
    BenchmarkingService
)


@pytest.fixture
def sample_diligence_states() -> List[DiligenceState]:
    inv1_id = str(uuid.uuid4())
    inv2_id = str(uuid.uuid4())

    state1 = DiligenceState(
        investment_id=inv1_id,
        company_name="AlphaTech AI",
        industry="Enterprise Software",
        target_round="Series A",
        check_size_usd=5_000_000.0,
        status=DiligenceStatus.COMPLETED,
        financial_metrics=[
            FinancialMetricRecord(metric_name="ARR", value=12.5, unit="USD", period="FY2024", formula="ARR"),
            FinancialMetricRecord(metric_name="Gross_Margin", value=82.0, unit="%", period="FY2024", formula="Gross Margin"),
            FinancialMetricRecord(metric_name="NRR", value=130.0, unit="%", period="FY2024", formula="NRR"),
            FinancialMetricRecord(metric_name="Runway", value=18.0, unit="months", period="FY2024", formula="Runway"),
            FinancialMetricRecord(metric_name="LTV_CAC", value=4.5, unit="x", period="FY2024", formula="LTV/CAC"),
        ],
        specialist_analyses={
            "Competitive": SpecialistAnalysis(
                domain="Competitive",
                summary="Strong moat powered by proprietary network effects and high switching costs.",
                strengths=["Proprietary AI model architecture", "Network effect with 500+ enterprise integrations"],
                confidence_score=0.9
            )
        },
        risk_register=[
            ClaimNode(
                text="Key person dependency on lead AI research scientist",
                claim_type=ClaimType.FACT,
                materiality=MaterialityLevel.HIGH,
                supporting_reasoning="Core IP generation heavily relies on single founder."
            )
        ],
        recommendation="INVEST",
        confidence_score=0.88
    )

    state2 = DiligenceState(
        investment_id=inv2_id,
        company_name="BetaCloud Inc",
        industry="Cloud Infrastructure",
        target_round="Series B",
        check_size_usd=10_000_000.0,
        status=DiligenceStatus.CROSS_EXAMINATION,
        financial_metrics=[
            FinancialMetricRecord(metric_name="ARR", value=5.0, unit="USD", period="FY2024", formula="ARR"),
            FinancialMetricRecord(metric_name="Gross_Margin", value=60.0, unit="%", period="FY2024", formula="Gross Margin"),
            FinancialMetricRecord(metric_name="NRR", value=95.0, unit="%", period="FY2024", formula="NRR"),
            FinancialMetricRecord(metric_name="Runway", value=4.0, unit="months", period="FY2024", formula="Runway"),
            FinancialMetricRecord(metric_name="Customer_Concentration", value=42.0, unit="%", period="FY2024", formula="Concentration"),
            FinancialMetricRecord(metric_name="LTV_CAC", value=2.1, unit="x", period="FY2024", formula="LTV/CAC"),
        ],
        contradictions=[
            ContradictionRecord(
                claim_a_id=str(uuid.uuid4()),
                claim_b_id=str(uuid.uuid4()),
                description="Pitch deck claims 50% YoY growth while audited financials indicate flat revenue.",
                materiality=MaterialityLevel.CRITICAL,
                status="OPEN"
            )
        ],
        recommendation="PASS",
        confidence_score=0.45
    )

    return [state1, state2]


def test_side_by_side_deal_comparison(sample_diligence_states: List[DiligenceState]):
    response: PortfolioComparisonResponse = generate_portfolio_comparison(sample_diligence_states)

    assert isinstance(response, PortfolioComparisonResponse)
    assert response.total_companies == 2
    assert len(response.companies) == 2

    # Check Company 1 (AlphaTech AI)
    comp1 = next(c for c in response.companies if c.company_name == "AlphaTech AI")
    assert comp1.arr == "$12.5M"
    assert comp1.gross_margin == "82%"
    assert comp1.nrr == "130%"
    assert comp1.runway == "18 months"
    assert comp1.ltv_cac == "4.5x"
    assert comp1.moat_strength == "Strong"
    assert comp1.recommendation == "INVEST"
    assert comp1.confidence_score == 0.88
    assert comp1.risk_count == 1
    assert len(comp1.dominant_risks) == 1

    # Check Company 2 (BetaCloud Inc)
    comp2 = next(c for c in response.companies if c.company_name == "BetaCloud Inc")
    assert comp2.arr == "$5M"
    assert comp2.gross_margin == "60%"
    assert comp2.nrr == "95%"
    assert comp2.runway == "4 months"
    assert comp2.ltv_cac == "2.1x"
    assert comp2.recommendation == "PASS"
    assert comp2.confidence_score == 0.45
    assert comp2.risk_count == 1  # 1 open contradiction


def test_critical_red_flag_detection_short_runway(sample_diligence_states: List[DiligenceState]):
    alerts: List[RedFlagAlert] = detect_portfolio_red_flags(sample_diligence_states)

    # BetaCloud Inc has Runway = 4 months (< 6 months)
    runway_alerts = [a for a in alerts if a.company_name == "BetaCloud Inc" and "Runway Shortage" in a.title]
    assert len(runway_alerts) == 1
    alert = runway_alerts[0]
    assert alert.severity == RedFlagSeverity.CRITICAL
    assert alert.materiality == MaterialityLevel.CRITICAL
    assert "4 months" in alert.description
    assert alert.category == "Financial / Runway"


def test_critical_red_flag_detection_high_concentration(sample_diligence_states: List[DiligenceState]):
    alerts: List[RedFlagAlert] = detect_portfolio_red_flags(sample_diligence_states)

    # BetaCloud Inc has Customer_Concentration = 42% (> 30%)
    conc_alerts = [a for a in alerts if a.company_name == "BetaCloud Inc" and "Customer Concentration" in a.title]
    assert len(conc_alerts) == 1
    alert = conc_alerts[0]
    assert alert.severity == RedFlagSeverity.CRITICAL
    assert alert.materiality == MaterialityLevel.CRITICAL
    assert "42%" in alert.description or "42" in alert.description
    assert alert.category == "Revenue Risk"


def test_unresolved_contradictions_and_low_confidence(sample_diligence_states: List[DiligenceState]):
    alerts: List[RedFlagAlert] = detect_portfolio_red_flags(sample_diligence_states)

    # Check unresolved contradiction alert
    contra_alerts = [a for a in alerts if a.company_name == "BetaCloud Inc" and a.category == "Cross-Examination"]
    assert len(contra_alerts) == 1
    assert contra_alerts[0].severity == RedFlagSeverity.CRITICAL
    assert "50% YoY growth" in contra_alerts[0].description

    # Check low confidence alert (< 60%)
    conf_alerts = [a for a in alerts if a.company_name == "BetaCloud Inc" and a.category == "Diligence Confidence"]
    assert len(conf_alerts) == 1
    assert conf_alerts[0].severity == RedFlagSeverity.HIGH
    assert "45%" in conf_alerts[0].description
