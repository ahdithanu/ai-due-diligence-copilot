import pytest
from backend.domain.schemas import (
    CapTableEntry,
    WaterfallPayout,
    WaterfallScenario,
    SensitivityScenario,
    SensitivityMatrix,
)
from backend.services.waterfall_calculator import (
    calculate_exit_waterfall,
    generate_waterfall_curve,
)
from backend.services.sensitivity_engine import run_sensitivity_stress_test

def test_schemas_instantiation():
    entry = CapTableEntry(
        share_class="Series A",
        investor_name="Founders Fund",
        shares_held=1000000.0,
        ownership_pct=20.0,
        liquidation_preference_multiplier=1.0,
        is_participating=False,
        cap_multiplier=None
    )
    assert entry.share_class == "Series A"
    assert entry.ownership_pct == 20.0

    payout = WaterfallPayout(
        share_class="Series A",
        investor_name="Founders Fund",
        payout_usd=5000000.0,
        moic=2.5,
        irr_pct=20.11
    )
    assert payout.payout_usd == 5000000.0

    scenario = WaterfallScenario(
        exit_valuation_usd=25000000.0,
        payouts=[payout]
    )
    assert scenario.exit_valuation_usd == 25000000.0
    assert len(scenario.payouts) == 1

def test_waterfall_calculator_non_participating():
    cap_table = [
        CapTableEntry(
            share_class="Series A Preferred",
            investor_name="VC Fund I",
            shares_held=2000000.0,
            ownership_pct=20.0,
            liquidation_preference_multiplier=1.0,
            is_participating=False,
        ),
        CapTableEntry(
            share_class="Common",
            investor_name="Founders",
            shares_held=8000000.0,
            ownership_pct=80.0,
            liquidation_preference_multiplier=0.0,
            is_participating=False,
        )
    ]

    scenario_low = calculate_exit_waterfall(cap_table, exit_valuation_usd=4000000.0, total_investment_usd=5000000.0)
    payout_vc_low = next(p for p in scenario_low.payouts if p.investor_name == "VC Fund I")
    payout_founder_low = next(p for p in scenario_low.payouts if p.investor_name == "Founders")
    assert payout_vc_low.payout_usd == 4000000.0
    assert payout_founder_low.payout_usd == 0.0

    scenario_mid = calculate_exit_waterfall(cap_table, exit_valuation_usd=10000000.0, total_investment_usd=5000000.0)
    payout_vc_mid = next(p for p in scenario_mid.payouts if p.investor_name == "VC Fund I")
    payout_founder_mid = next(p for p in scenario_mid.payouts if p.investor_name == "Founders")
    assert payout_vc_mid.payout_usd == 5000000.0
    assert payout_founder_mid.payout_usd == 5000000.0

    scenario_high = calculate_exit_waterfall(cap_table, exit_valuation_usd=50000000.0, total_investment_usd=5000000.0)
    payout_vc_high = next(p for p in scenario_high.payouts if p.investor_name == "VC Fund I")
    payout_founder_high = next(p for p in scenario_high.payouts if p.investor_name == "Founders")
    assert payout_vc_high.payout_usd == 10000000.0
    assert payout_founder_high.payout_usd == 40000000.0

def test_waterfall_calculator_participating_with_cap():
    cap_table = [
        CapTableEntry(
            share_class="Series B Preferred",
            investor_name="Growth Fund",
            shares_held=3000000.0,
            ownership_pct=30.0,
            liquidation_preference_multiplier=1.0,
            is_participating=True,
            cap_multiplier=2.0,
        ),
        CapTableEntry(
            share_class="Common",
            investor_name="Founders",
            shares_held=7000000.0,
            ownership_pct=70.0,
            liquidation_preference_multiplier=0.0,
            is_participating=False,
        )
    ]

    scenario = calculate_exit_waterfall(cap_table, exit_valuation_usd=30000000.0, total_investment_usd=10000000.0)
    payout_gf = next(p for p in scenario.payouts if p.investor_name == "Growth Fund")
    payout_founder = next(p for p in scenario.payouts if p.investor_name == "Founders")
    assert payout_gf.payout_usd == 16000000.0
    assert payout_founder.payout_usd == 14000000.0

def test_generate_waterfall_curve():
    cap_table = [
        CapTableEntry(
            share_class="Common",
            investor_name="Founders",
            shares_held=1000000.0,
            ownership_pct=100.0,
            liquidation_preference_multiplier=0.0,
        )
    ]
    valuations = [1000000.0, 5000000.0, 10000000.0]
    scenarios = generate_waterfall_curve(cap_table, valuations)
    assert len(scenarios) == 3
    assert scenarios[0].exit_valuation_usd == 1000000.0
    assert scenarios[2].payouts[0].payout_usd == 10000000.0

def test_sensitivity_engine():
    metrics = {
        "runway_months": 18.0,
        "ebitda_margin_pct": -10.0,
        "revenue_growth_pct": 30.0,
        "churn_pct": 4.0,
        "gross_margin_pct": 75.0,
        "cac_payback_months": 12.0
    }
    matrix = run_sensitivity_stress_test(metrics)
    assert matrix.base_runway_months == 18.0
    assert matrix.base_ebitda_margin_pct == -10.0
    assert len(matrix.scenarios) == 5

    names = [s.scenario_name for s in matrix.scenarios]
    assert "Base Case" in names
    assert "Moderate Growth Miss" in names
    assert "Churn Spike" in names
    assert "Severe Macro Downturn" in names
    assert "Optimistic Upside" in names

    base_scenario = next(s for s in matrix.scenarios if s.scenario_name == "Base Case")
    assert base_scenario.resulting_runway_months == 18.0
    assert base_scenario.resulting_ebitda_margin_pct == -10.0

    severe_scenario = next(s for s in matrix.scenarios if s.scenario_name == "Severe Macro Downturn")
    assert severe_scenario.risk_level == "CRITICAL"
    assert severe_scenario.revenue_growth_delta_pct == -30.0
    assert severe_scenario.churn_delta_pct == 8.0
    assert severe_scenario.resulting_runway_months < 18.0
