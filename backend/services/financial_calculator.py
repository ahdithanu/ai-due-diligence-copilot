import re
import uuid
from typing import List, Optional, Dict, Any
from backend.domain.schemas import FinancialMetricRecord, DiligenceState, EvidenceRecord

def calculate_revenue_growth(
    current_revenue: float,
    prior_revenue: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    if prior_revenue == 0:
        return None
    val = ((current_revenue - prior_revenue) / abs(prior_revenue)) * 100.0
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Revenue_Growth",
        value=round(val, 4),
        unit="percentage",
        period=period or "N/A",
        formula="(Current_Revenue - Prior_Revenue) / Prior_Revenue * 100",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_gross_margin(
    revenue: float,
    cogs: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    if revenue == 0:
        return None
    val = ((revenue - cogs) / revenue) * 100.0
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Gross_Margin",
        value=round(val, 4),
        unit="percentage",
        period=period or "N/A",
        formula="(Revenue - COGS) / Revenue * 100",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_operating_margin(
    operating_income: float,
    revenue: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    if revenue == 0:
        return None
    val = (operating_income / revenue) * 100.0
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Operating_Margin",
        value=round(val, 4),
        unit="percentage",
        period=period or "N/A",
        formula="Operating_Income / Revenue * 100",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_ebitda_margin(
    ebitda: float,
    revenue: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    if revenue == 0:
        return None
    val = (ebitda / revenue) * 100.0
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="EBITDA_Margin",
        value=round(val, 4),
        unit="percentage",
        period=period or "N/A",
        formula="EBITDA / Revenue * 100",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_burn_rate(
    cash_outflow: float,
    cash_inflow: float = 0.0,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    val = cash_outflow - cash_inflow
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Burn_Rate",
        value=round(val, 4),
        unit="USD",
        period=period or "N/A",
        formula="Cash_Outflow - Cash_Inflow",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_runway(
    cash_balance: float,
    monthly_burn_rate: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    if monthly_burn_rate <= 0:
        return None
    val = cash_balance / monthly_burn_rate
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Runway",
        value=round(val, 4),
        unit="months",
        period=period or "N/A",
        formula="Cash_Balance / Monthly_Burn_Rate",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_arr(
    mrr: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    val = mrr * 12.0
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="ARR",
        value=round(val, 4),
        unit="USD",
        period=period or "N/A",
        formula="MRR * 12",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_mrr(
    arr: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    val = arr / 12.0
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="MRR",
        value=round(val, 4),
        unit="USD",
        period=period or "N/A",
        formula="ARR / 12",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_nrr(
    starting_mrr: float,
    expansion: float = 0.0,
    contraction: float = 0.0,
    churn: float = 0.0,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    if starting_mrr == 0:
        return None
    val = ((starting_mrr + expansion - contraction - churn) / starting_mrr) * 100.0
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Net_Revenue_Retention",
        value=round(val, 4),
        unit="percentage",
        period=period or "N/A",
        formula="(Starting_MRR + Expansion - Contraction - Churn) / Starting_MRR * 100",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_customer_concentration(
    top_customer_revenue: float,
    total_revenue: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    if total_revenue == 0:
        return None
    val = (top_customer_revenue / total_revenue) * 100.0
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Customer_Concentration",
        value=round(val, 4),
        unit="percentage",
        period=period or "N/A",
        formula="Top_Customer_Revenue / Total_Revenue * 100",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_cac(
    sales_marketing_expense: float,
    new_customers_acquired: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    if new_customers_acquired == 0:
        return None
    val = sales_marketing_expense / new_customers_acquired
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="CAC",
        value=round(val, 4),
        unit="USD",
        period=period or "N/A",
        formula="Sales_Marketing_Expense / New_Customers_Acquired",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_ltv(
    arpu: float,
    gross_margin_pct: float,
    churn_rate_pct: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    if churn_rate_pct == 0:
        return None
    val = (arpu * (gross_margin_pct / 100.0)) / (churn_rate_pct / 100.0)
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="LTV",
        value=round(val, 4),
        unit="USD",
        period=period or "N/A",
        formula="(ARPU * (Gross_Margin_Pct / 100)) / (Churn_Rate_Pct / 100)",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_ltv_cac(
    ltv: float,
    cac: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    if cac == 0:
        return None
    val = ltv / cac
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="LTV_CAC",
        value=round(val, 4),
        unit="ratio",
        period=period or "N/A",
        formula="LTV / CAC",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_cac_payback(
    cac: float,
    arpu: float,
    gross_margin_pct: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    denom = arpu * (gross_margin_pct / 100.0)
    if denom == 0:
        return None
    val = cac / denom
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="CAC_Payback",
        value=round(val, 4),
        unit="months",
        period=period or "N/A",
        formula="CAC / (ARPU * (Gross_Margin_Pct / 100))",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_rule_of_40(
    revenue_growth_pct: float,
    profit_margin_pct: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    val = revenue_growth_pct + profit_margin_pct
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Rule_of_40",
        value=round(val, 4),
        unit="percentage",
        period=period or "N/A",
        formula="Revenue_Growth_Pct + Profit_Margin_Pct",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_cash_conversion(
    free_cash_flow: float,
    ebitda: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    if ebitda == 0:
        return None
    val = (free_cash_flow / ebitda) * 100.0
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Cash_Conversion",
        value=round(val, 4),
        unit="percentage",
        period=period or "N/A",
        formula="Free_Cash_Flow / EBITDA * 100",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_working_capital(
    current_assets: float,
    current_liabilities: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    val = current_assets - current_liabilities
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Working_Capital",
        value=round(val, 4),
        unit="USD",
        period=period or "N/A",
        formula="Current_Assets - Current_Liabilities",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )


# --- CRE Small-Bay Retail & Multifamily "Buy Box" Deterministic Calculations ---

def calculate_price_per_sf(
    purchase_price: float,
    total_sf: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    """
    Calculates acquisition price per square foot.
    Buy box target: $100 - $200 / SF.
    """
    if total_sf <= 0:
        return None
    val = purchase_price / total_sf
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Price_Per_SF",
        value=round(val, 2),
        unit="USD/SF",
        period=period or "N/A",
        formula="Purchase_Price / Total_SF",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_cre_occupancy(
    occupied_sf: float,
    total_sf: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    """
    Calculates physical or economic occupancy rate percentage.
    Buy box target: 80.0% - 100.0% (max 20% vacancy).
    """
    if total_sf <= 0:
        return None
    val = (occupied_sf / total_sf) * 100.0
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Occupancy_Rate",
        value=round(val, 2),
        unit="percentage",
        period=period or "N/A",
        formula="(Occupied_SF / Total_SF) * 100",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_tenant_concentration(
    top_tenant_rent: float,
    total_gross_rent: float,
    tenant_name: str = "Top_Tenant",
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    """
    Calculates single tenant rent concentration percentage.
    Buy box rule: No single tenant > 30% of gross rent.
    """
    if total_gross_rent <= 0:
        return None
    val = (top_tenant_rent / total_gross_rent) * 100.0
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name=f"Tenant_Concentration_{tenant_name.replace(' ', '_')}",
        value=round(val, 2),
        unit="percentage",
        period=period or "N/A",
        formula="(Top_Tenant_Rent / Total_Gross_Rent) * 100",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_restaurant_exposure(
    restaurant_rent: float,
    total_gross_rent: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    """
    Calculates restaurant tenant exposure as a percentage of total rent roll.
    Buy box rule: Restaurants capped strictly under 25% of rent roll.
    """
    if total_gross_rent <= 0:
        return None
    val = (restaurant_rent / total_gross_rent) * 100.0
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Restaurant_Exposure",
        value=round(val, 2),
        unit="percentage",
        period=period or "N/A",
        formula="(Restaurant_Rent / Total_Gross_Rent) * 100",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_walt(
    lease_terms: List[Dict[str, float]],
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    """
    Calculates Weighted Average Lease Term (WALT) in years:
    Sum(Annual_Rent * Remaining_Years) / Sum(Annual_Rent).
    Buy box rule: WALT >= 3.0 years.
    Each item in lease_terms must have keys: 'annual_rent' (or 'rent') and 'remaining_years' (or 'years').
    """
    total_rent = 0.0
    weighted_years_sum = 0.0

    for lease in lease_terms:
        rent = lease.get("annual_rent", lease.get("rent", 0.0))
        years = lease.get("remaining_years", lease.get("years", 0.0))
        if rent > 0 and years >= 0:
            total_rent += rent
            weighted_years_sum += rent * years

    if total_rent <= 0:
        return None

    val = weighted_years_sum / total_rent
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="WALT",
        value=round(val, 2),
        unit="years",
        period=period or "N/A",
        formula="Sum(Annual_Rent * Remaining_Years) / Sum(Annual_Rent)",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )

def calculate_parking_ratio(
    parking_spaces: int,
    total_sf: float,
    period: str = "N/A",
    evidence_ids: Optional[List[str]] = None
) -> Optional[FinancialMetricRecord]:
    """
    Calculates parking ratio per 1,000 square feet.
    Buy box rule: At least 4.0 parking spaces per 1,000 SF.
    """
    if total_sf <= 0:
        return None
    val = float(parking_spaces) / (total_sf / 1000.0)
    return FinancialMetricRecord(
        id=str(uuid.uuid4()),
        metric_name="Parking_Ratio",
        value=round(val, 2),
        unit="spaces_per_1000_sf",
        period=period or "N/A",
        formula="Parking_Spaces / (Total_SF / 1000)",
        input_evidence_ids=evidence_ids or [],
        is_deterministic=True,
        confidence=1.0
    )


def extract_and_calculate_metrics(state: DiligenceState) -> List[FinancialMetricRecord]:
    """
    Parses financial inputs from state.evidence_records (or metadata) and executes all available
    deterministic calculations.
    """
    calculated_metrics: List[FinancialMetricRecord] = []

    # Map to hold extracted financial parameters per period
    # e.g., params[period]['revenue'] = (value, evidence_id)
    extracted: Dict[str, Dict[str, Any]] = {}

    def set_param(period: str, key: str, val: float, ev_id: str):
        if period not in extracted:
            extracted[period] = {}
        if key not in extracted[period]:
            extracted[period][key] = (val, [ev_id])
        else:
            current_val, ev_ids = extracted[period][key]
            if ev_id not in ev_ids:
                ev_ids.append(ev_id)

    # Patterns for parsing evidence content
    number_pattern = r"(?:\$?\s*([\d,]+(?:\.\d+)?)\s*(M|B|K|k|million|billion|%)?)"

    # Period detector pattern (e.g. FY2024, Q4 2024, 2023)
    period_pattern = re.compile(r"\b(FY\s*\d{4}|Q[1-4]\s*\d{4}|\d{4})\b", re.IGNORECASE)

    patterns = {
        "mrr": re.compile(r"\bMRR\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "arr": re.compile(r"\bARR\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "revenue": re.compile(r"\bCurrent\s+Revenue|\bRevenue\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "prior_revenue": re.compile(r"\bPrior\s+Revenue\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "cogs": re.compile(r"\bCOGS\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "operating_income": re.compile(r"\bOperating\s+Income\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "ebitda": re.compile(r"\bEBITDA\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "cash_balance": re.compile(r"\bCash\s+Balance|\bCash\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "monthly_burn": re.compile(r"\bMonthly\s+Burn(?:\s+Rate)?\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "cash_outflow": re.compile(r"\bCash\s+Outflow\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "cash_inflow": re.compile(r"\bCash\s+Inflow\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "starting_mrr": re.compile(r"\bStarting\s+MRR\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "expansion": re.compile(r"\bExpansion\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "contraction": re.compile(r"\bContraction\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "churn": re.compile(r"\bChurn\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "top_customer_revenue": re.compile(r"\bTop\s+Customer\s+Revenue\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "total_revenue": re.compile(r"\bTotal\s+Revenue\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "sales_marketing_expense": re.compile(r"\bSales\s*(?:&|\band\b)?\s*Marketing\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "new_customers": re.compile(r"\bNew\s+Customers\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "arpu": re.compile(r"\bARPU\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "gross_margin_pct": re.compile(r"\bGross\s+Margin\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "churn_rate_pct": re.compile(r"\bChurn\s+Rate\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "ltv": re.compile(r"\bLTV\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "cac": re.compile(r"\bCAC\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "revenue_growth_pct": re.compile(r"\bRevenue\s+Growth\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "profit_margin_pct": re.compile(r"\bProfit\s+Margin\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "free_cash_flow": re.compile(r"\bFree\s+Cash\s+Flow|\bFCF\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "current_assets": re.compile(r"\bCurrent\s+Assets\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
        "current_liabilities": re.compile(r"\bCurrent\s+Liabilities\b[^\n.]{0,30}?" + number_pattern, re.IGNORECASE),
    }


    def parse_num_match(raw_num: Optional[str], mult: Optional[str]) -> float:
        if not raw_num:
            return 0.0
        clean = raw_num.replace(",", "").strip()
        val = float(clean)
        if mult:
            m = mult.lower().strip()
            if m in ["m", "million"]:
                val *= 1_000_000.0
            elif m in ["b", "billion"]:
                val *= 1_000_000_000.0
            elif m in ["k"]:
                val *= 1_000.0
        return val


    for record in state.evidence_records:
        text = record.content
        period_match = period_pattern.search(text)
        period = period_match.group(1).upper().replace(" ", "_") if period_match else "N/A"

        # Check metadata first if present
        if record.metadata and isinstance(record.metadata, dict):
            for k, v in record.metadata.items():
                if k in patterns and isinstance(v, (int, float)):
                    set_param(period, k, float(v), record.id)

        # Parse text against regex patterns
        for key, pat in patterns.items():
            match = pat.search(text)
            if match:
                raw_num, mult = match.group(1), match.group(2)
                try:
                    num_val = parse_num_match(raw_num, mult)
                    set_param(period, key, num_val, record.id)
                except (ValueError, TypeError):
                    continue

    # Execute calculations for all extracted period parameter sets
    for period, params in extracted.items():
        # ARR from MRR
        if "mrr" in params and "arr" not in params:
            mrr_val, ev_ids = params["mrr"]
            rec = calculate_arr(mrr_val, period=period, evidence_ids=ev_ids)
            if rec:
                calculated_metrics.append(rec)
        # MRR from ARR
        if "arr" in params and "mrr" not in params:
            arr_val, ev_ids = params["arr"]
            rec = calculate_mrr(arr_val, period=period, evidence_ids=ev_ids)
            if rec:
                calculated_metrics.append(rec)
        # Revenue Growth
        if "revenue" in params and "prior_revenue" in params:
            rev_val, rev_ids = params["revenue"]
            p_rev_val, p_rev_ids = params["prior_revenue"]
            rec = calculate_revenue_growth(rev_val, p_rev_val, period=period, evidence_ids=list(set(rev_ids + p_rev_ids)))
            if rec:
                calculated_metrics.append(rec)
        # Gross Margin
        if "revenue" in params and "cogs" in params:
            rev_val, rev_ids = params["revenue"]
            cogs_val, cogs_ids = params["cogs"]
            rec = calculate_gross_margin(rev_val, cogs_val, period=period, evidence_ids=list(set(rev_ids + cogs_ids)))
            if rec:
                calculated_metrics.append(rec)
        # Operating Margin
        if "operating_income" in params and "revenue" in params:
            op_val, op_ids = params["operating_income"]
            rev_val, rev_ids = params["revenue"]
            rec = calculate_operating_margin(op_val, rev_val, period=period, evidence_ids=list(set(op_ids + rev_ids)))
            if rec:
                calculated_metrics.append(rec)
        # EBITDA Margin
        if "ebitda" in params and "revenue" in params:
            eb_val, eb_ids = params["ebitda"]
            rev_val, rev_ids = params["revenue"]
            rec = calculate_ebitda_margin(eb_val, rev_val, period=period, evidence_ids=list(set(eb_ids + rev_ids)))
            if rec:
                calculated_metrics.append(rec)
        # Burn Rate
        if "cash_outflow" in params:
            out_val, out_ids = params["cash_outflow"]
            in_val, in_ids = params.get("cash_inflow", (0.0, []))
            rec = calculate_burn_rate(out_val, in_val, period=period, evidence_ids=list(set(out_ids + in_ids)))
            if rec:
                calculated_metrics.append(rec)
        # Runway
        if "cash_balance" in params and "monthly_burn" in params:
            cash_val, cash_ids = params["cash_balance"]
            burn_val, burn_ids = params["monthly_burn"]
            rec = calculate_runway(cash_val, burn_val, period=period, evidence_ids=list(set(cash_ids + burn_ids)))
            if rec:
                calculated_metrics.append(rec)
        # NRR
        if "starting_mrr" in params:
            st_mrr, st_ids = params["starting_mrr"]
            exp, exp_ids = params.get("expansion", (0.0, []))
            con, con_ids = params.get("contraction", (0.0, []))
            ch, ch_ids = params.get("churn", (0.0, []))
            rec = calculate_nrr(st_mrr, exp, con, ch, period=period, evidence_ids=list(set(st_ids + exp_ids + con_ids + ch_ids)))
            if rec:
                calculated_metrics.append(rec)
        # Customer Concentration
        if "top_customer_revenue" in params and ("total_revenue" in params or "revenue" in params):
            top_val, top_ids = params["top_customer_revenue"]
            tot_tuple = params.get("total_revenue", params.get("revenue"))
            tot_val, tot_ids = tot_tuple
            rec = calculate_customer_concentration(top_val, tot_val, period=period, evidence_ids=list(set(top_ids + tot_ids)))
            if rec:
                calculated_metrics.append(rec)
        # CAC
        if "sales_marketing_expense" in params and "new_customers" in params:
            sm_val, sm_ids = params["sales_marketing_expense"]
            cust_val, cust_ids = params["new_customers"]
            rec = calculate_cac(sm_val, cust_val, period=period, evidence_ids=list(set(sm_ids + cust_ids)))
            if rec:
                calculated_metrics.append(rec)
        # LTV
        if "arpu" in params and "gross_margin_pct" in params and "churn_rate_pct" in params:
            arpu_val, arpu_ids = params["arpu"]
            gm_val, gm_ids = params["gross_margin_pct"]
            ch_val, ch_ids = params["churn_rate_pct"]
            rec = calculate_ltv(arpu_val, gm_val, ch_val, period=period, evidence_ids=list(set(arpu_ids + gm_ids + ch_ids)))
            if rec:
                calculated_metrics.append(rec)
        # LTV / CAC
        if "ltv" in params and "cac" in params:
            ltv_val, ltv_ids = params["ltv"]
            cac_val, cac_ids = params["cac"]
            rec = calculate_ltv_cac(ltv_val, cac_val, period=period, evidence_ids=list(set(ltv_ids + cac_ids)))
            if rec:
                calculated_metrics.append(rec)
        # CAC Payback
        if "cac" in params and "arpu" in params and "gross_margin_pct" in params:
            cac_val, cac_ids = params["cac"]
            arpu_val, arpu_ids = params["arpu"]
            gm_val, gm_ids = params["gross_margin_pct"]
            rec = calculate_cac_payback(cac_val, arpu_val, gm_val, period=period, evidence_ids=list(set(cac_ids + arpu_ids + gm_ids)))
            if rec:
                calculated_metrics.append(rec)
        # Rule of 40
        if "revenue_growth_pct" in params and "profit_margin_pct" in params:
            rg_val, rg_ids = params["revenue_growth_pct"]
            pm_val, pm_ids = params["profit_margin_pct"]
            rec = calculate_rule_of_40(rg_val, pm_val, period=period, evidence_ids=list(set(rg_ids + pm_ids)))
            if rec:
                calculated_metrics.append(rec)
        # Cash Conversion
        if "free_cash_flow" in params and "ebitda" in params:
            fcf_val, fcf_ids = params["free_cash_flow"]
            eb_val, eb_ids = params["ebitda"]
            rec = calculate_cash_conversion(fcf_val, eb_val, period=period, evidence_ids=list(set(fcf_ids + eb_ids)))
            if rec:
                calculated_metrics.append(rec)
        # Working Capital
        if "current_assets" in params and "current_liabilities" in params:
            ca_val, ca_ids = params["current_assets"]
            cl_val, cl_ids = params["current_liabilities"]
            rec = calculate_working_capital(ca_val, cl_val, period=period, evidence_ids=list(set(ca_ids + cl_ids)))
            if rec:
                calculated_metrics.append(rec)

    return calculated_metrics
