from typing import Dict, Any, List
from backend.domain.schemas import SensitivityScenario, SensitivityMatrix

def run_sensitivity_stress_test(financial_metrics: Dict[str, float]) -> SensitivityMatrix:
    """
    Calculates stress-tested runway and EBITDA margin under 5 scenarios:
    Base Case, Moderate Growth Miss (-15%), Churn Spike (+5%),
    Severe Macro Downturn (-30% growth, +20% CAC, +8% churn), and Optimistic Upside (+25% growth).
    """
    base_runway = float(financial_metrics.get("runway_months", financial_metrics.get("runway", 18.0)))
    base_ebitda = float(financial_metrics.get("ebitda_margin_pct", financial_metrics.get("ebitda_margin", -15.0)))
    base_cac = float(financial_metrics.get("cac_payback_months", financial_metrics.get("cac_payback", 12.0)))

    scenario_configs = [
        {
            "name": "Base Case",
            "growth_delta": 0.0,
            "churn_delta": 0.0,
            "gm_delta": 0.0,
            "cac_delta": 0.0,
            "risk": "LOW"
        },
        {
            "name": "Moderate Growth Miss",
            "growth_delta": -15.0,
            "churn_delta": 0.0,
            "gm_delta": -2.0,
            "cac_delta": 2.0,
            "risk": "MEDIUM"
        },
        {
            "name": "Churn Spike",
            "growth_delta": -5.0,
            "churn_delta": 5.0,
            "gm_delta": -3.0,
            "cac_delta": 3.0,
            "risk": "HIGH"
        },
        {
            "name": "Severe Macro Downturn",
            "growth_delta": -30.0,
            "churn_delta": 8.0,
            "gm_delta": -8.0,
            "cac_delta": round(base_cac * 0.20, 2),
            "risk": "CRITICAL"
        },
        {
            "name": "Optimistic Upside",
            "growth_delta": 25.0,
            "churn_delta": -2.0,
            "gm_delta": 4.0,
            "cac_delta": -2.0,
            "risk": "LOW"
        }
    ]

    scenarios: List[SensitivityScenario] = []

    for cfg in scenario_configs:
        growth_d = cfg["growth_delta"]
        churn_d = cfg["churn_delta"]
        gm_d = cfg["gm_delta"]
        cac_d = cfg["cac_delta"]

        ebitda_delta = (0.4 * growth_d) - (0.8 * churn_d) + (1.0 * gm_d) - (0.5 * cac_d)
        res_ebitda = round(base_ebitda + ebitda_delta, 2)

        runway_delta = (0.25 * growth_d) - (0.8 * churn_d) + (0.15 * gm_d) - (0.6 * cac_d)
        res_runway = max(1.0, round(base_runway + runway_delta, 2))

        scenarios.append(
            SensitivityScenario(
                scenario_name=cfg["name"],
                revenue_growth_delta_pct=float(growth_d),
                churn_delta_pct=float(churn_d),
                gross_margin_delta_pct=float(gm_d),
                cac_payback_delta_months=float(cac_d),
                resulting_runway_months=res_runway,
                resulting_ebitda_margin_pct=res_ebitda,
                risk_level=cfg["risk"]
            )
        )

    return SensitivityMatrix(
        base_runway_months=base_runway,
        base_ebitda_margin_pct=base_ebitda,
        scenarios=scenarios
    )
