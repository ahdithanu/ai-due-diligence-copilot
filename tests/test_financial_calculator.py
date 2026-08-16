import pytest
from backend.domain.schemas import DiligenceState, EvidenceRecord, ClaimType
from backend.services.financial_calculator import (
    calculate_revenue_growth,
    calculate_gross_margin,
    calculate_operating_margin,
    calculate_ebitda_margin,
    calculate_burn_rate,
    calculate_runway,
    calculate_arr,
    calculate_mrr,
    calculate_nrr,
    calculate_customer_concentration,
    calculate_cac,
    calculate_ltv,
    calculate_ltv_cac,
    calculate_cac_payback,
    calculate_rule_of_40,
    calculate_cash_conversion,
    calculate_working_capital,
    extract_and_calculate_metrics
)

def test_exact_mathematical_formulas():
    # 1. ARR & MRR
    arr_rec = calculate_arr(mrr=100000.0, period="FY2024", evidence_ids=["ev1"])
    assert arr_rec is not None
    assert arr_rec.value == 1200000.0
    assert arr_rec.unit == "USD"
    assert arr_rec.period == "FY2024"
    assert arr_rec.input_evidence_ids == ["ev1"]
    assert arr_rec.is_deterministic is True
    assert arr_rec.confidence == 1.0

    mrr_rec = calculate_mrr(arr=1200000.0, period="FY2024")
    assert mrr_rec is not None
    assert mrr_rec.value == 100000.0

    # 2. Revenue Growth
    rev_growth = calculate_revenue_growth(current_revenue=15000000.0, prior_revenue=10000000.0, period="FY2024")
    assert rev_growth is not None
    assert rev_growth.value == 50.0

    # 3. Gross Margin
    gm = calculate_gross_margin(revenue=10000000.0, cogs=2000000.0, period="FY2024")
    assert gm is not None
    assert gm.value == 80.0

    # 4. Operating Margin
    op_m = calculate_operating_margin(operating_income=3000000.0, revenue=10000000.0)
    assert op_m is not None
    assert op_m.value == 30.0

    # 5. EBITDA Margin
    eb_m = calculate_ebitda_margin(ebitda=4000000.0, revenue=10000000.0)
    assert eb_m is not None
    assert eb_m.value == 40.0

    # 6. Burn Rate
    burn = calculate_burn_rate(cash_outflow=500000.0, cash_inflow=200000.0)
    assert burn is not None
    assert burn.value == 300000.0

    # 7. Runway
    rw = calculate_runway(cash_balance=3000000.0, monthly_burn_rate=300000.0)
    assert rw is not None
    assert rw.value == 10.0

    # 8. NRR
    nrr = calculate_nrr(starting_mrr=100000.0, expansion=20000.0, contraction=5000.0, churn=5000.0)
    assert nrr is not None
    assert nrr.value == 110.0

    # 9. Customer Concentration
    cc = calculate_customer_concentration(top_customer_revenue=2500000.0, total_revenue=10000000.0)
    assert cc is not None
    assert cc.value == 25.0

    # 10. CAC
    cac = calculate_cac(sales_marketing_expense=500000.0, new_customers_acquired=50.0)
    assert cac is not None
    assert cac.value == 10000.0

    # 11. LTV
    ltv = calculate_ltv(arpu=1000.0, gross_margin_pct=80.0, churn_rate_pct=2.0)
    assert ltv is not None
    assert ltv.value == 40000.0

    # 12. LTV/CAC
    ltv_cac = calculate_ltv_cac(ltv=40000.0, cac=10000.0)
    assert ltv_cac is not None
    assert ltv_cac.value == 4.0

    # 13. CAC Payback
    payback = calculate_cac_payback(cac=10000.0, arpu=1000.0, gross_margin_pct=80.0)
    assert payback is not None
    assert payback.value == 12.5

    # 14. Rule of 40
    r40 = calculate_rule_of_40(revenue_growth_pct=30.0, profit_margin_pct=15.0)
    assert r40 is not None
    assert r40.value == 45.0

    # 15. Cash Conversion
    cc_score = calculate_cash_conversion(free_cash_flow=2000000.0, ebitda=2500000.0)
    assert cc_score is not None
    assert cc_score.value == 80.0

    # 16. Working Capital
    wc = calculate_working_capital(current_assets=5000000.0, current_liabilities=2000000.0)
    assert wc is not None
    assert wc.value == 3000000.0


def test_zero_division_and_missing_period_handling():
    # Zero division returns None safely
    assert calculate_revenue_growth(100.0, 0.0) is None
    assert calculate_gross_margin(0.0, 10.0) is None
    assert calculate_operating_margin(10.0, 0.0) is None
    assert calculate_ebitda_margin(10.0, 0.0) is None
    assert calculate_runway(1000.0, 0.0) is None
    assert calculate_runway(1000.0, -100.0) is None
    assert calculate_nrr(0.0, 10.0, 0.0, 0.0) is None
    assert calculate_customer_concentration(10.0, 0.0) is None
    assert calculate_cac(100.0, 0.0) is None
    assert calculate_ltv(100.0, 80.0, 0.0) is None
    assert calculate_ltv_cac(100.0, 0.0) is None
    assert calculate_cac_payback(100.0, 0.0, 80.0) is None
    assert calculate_cac_payback(100.0, 10.0, 0.0) is None
    assert calculate_cash_conversion(100.0, 0.0) is None

    # Missing period defaults to 'N/A'
    arr_no_period = calculate_arr(mrr=5000.0)
    assert arr_no_period is not None
    assert arr_no_period.period == "N/A"


def test_extract_and_calculate_metrics():
    state = DiligenceState(
        investment_id="inv_123",
        company_name="Test Co",
        industry="SaaS",
        target_round="Series A"
    )

    ev1 = EvidenceRecord(
        document_id="doc1",
        chunk_id="chk1",
        content="MRR is $100K in FY2024.",
        claim_type=ClaimType.FACT
    )
    ev2 = EvidenceRecord(
        document_id="doc1",
        chunk_id="chk2",
        content="Revenue is $10M and COGS is $2M in FY2024.",
        claim_type=ClaimType.FACT
    )
    state.evidence_records.extend([ev1, ev2])

    metrics = extract_and_calculate_metrics(state)
    assert len(metrics) >= 2
    
    metric_names = [m.metric_name for m in metrics]
    assert "ARR" in metric_names
    assert "Gross_Margin" in metric_names

    arr_m = next(m for m in metrics if m.metric_name == "ARR")
    assert arr_m.value == 1200000.0
    assert arr_m.period == "FY2024"
    assert ev1.id in arr_m.input_evidence_ids

    gm_m = next(m for m in metrics if m.metric_name == "Gross_Margin")
    assert gm_m.value == 80.0
    assert gm_m.period == "FY2024"
    assert ev2.id in gm_m.input_evidence_ids
