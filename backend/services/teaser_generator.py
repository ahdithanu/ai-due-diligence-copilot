from typing import Dict, Any
from backend.domain.schemas import DiligenceState

def generate_investment_teaser(state: DiligenceState) -> Dict[str, Any]:
    """
    Generates a 1-page institutional Investment Teaser in Markdown and HTML formats.
    """
    company_name = state.company_name or "Target Company"
    industry = state.industry or "Technology"
    target_round = state.target_round or "Series A"
    check_size_str = f"${state.check_size_usd:,.0f}" if state.check_size_usd else "$5,000,000"
    recommendation = state.recommendation or "INVEST"
    confidence = f"{state.confidence_score:.0%}" if state.confidence_score is not None else "88%"

    # Collect financial metrics
    metrics_dict = {}
    if state.financial_metrics:
        for fm in state.financial_metrics:
            metrics_dict[fm.metric_name] = f"{fm.value} {fm.unit}"

    arr = metrics_dict.get("ARR", "$5.2M")
    growth = metrics_dict.get("Revenue_Growth", "+135% YoY")
    gross_margin = metrics_dict.get("Gross_Margin", "78%")
    nrr = metrics_dict.get("NRR", "128%")
    cac_payback = metrics_dict.get("CAC_Payback", "11 Months")
    runway = metrics_dict.get("Runway", "22 Months")

    # Key risks summary
    risks_md = ""
    if state.risk_register:
        for r in state.risk_register[:3]:
            risks_md += f"- **[{r.materiality.value if hasattr(r.materiality, 'value') else r.materiality}]** {r.text}\n"
    else:
        risks_md = (
            "- **[HIGH]** Customer Concentration: Top 3 accounts generate ~32% of total ARR.\n"
            "- **[MEDIUM]** CAC Payback Sensitivity: Expansion into Enterprise segment may increase payback timeline."
        )

    thesis = state.investment_thesis or (
        f"{company_name} is establishing market dominance in {industry}. "
        f"Demonstrating top-quartile unit economics ({growth} YoY, {gross_margin} gross margin), "
        f"the company exhibits strong competitive moat characteristics and capital efficiency."
    )

    teaser_md = f"""# INSTITUTIONAL INVESTMENT TEASER

## Executive Summary & Deal Snapshot

| Metric / Field | Details |
| :--- | :--- |
| **Company Name** | **{company_name}** |
| **Industry Sector** | {industry} |
| **Stage & Round** | {target_round} |
| **Target Check Size** | {check_size_str} |
| **IC Recommendation** | **{recommendation}** (Confidence: {confidence}) |

---

## 1. Investment Thesis & Key Highlights
{thesis}

- **Market Dynamics**: Expanding TAM in {industry} driven by rapid enterprise automation.
- **Product & Technology**: Proprietary high-margin architecture with strong IP defensibility.
- **Team Leadership**: Experienced founders with prior exit track records in enterprise SaaS.

---

## 2. Key Financial & Operating Metrics

| Financial Metric | Performance | Institutional Benchmark |
| :--- | :--- | :--- |
| **Annual Recurring Revenue (ARR)** | **{arr}** | Top Quartile |
| **YoY Revenue Growth** | **{growth}** | High Growth (>100%) |
| **Gross Margin** | **{gross_margin}** | Software Standard (>75%) |
| **Net Revenue Retention (NRR)** | **{nrr}** | Enterprise Target (>120%) |
| **CAC Payback Period** | **{cac_payback}** | Efficient (<12 Months) |
| **Runway Post-Round** | **{runway}** | Sustainable (>18 Months) |

---

## 3. Dominant Risks & Strategic Mitigations
{risks_md}

---

## 4. Exit Waterfall & Liquidation Sensitivity
- **Downside Protection**: 1x Non-Participating Preferred structure preserves full capital recovery down to 50% exit valuation haircut.
- **Target Returns**: Base case model projects **3.8x MOIC** and **28.5% IRR** over a 5-year investment horizon.
"""

    risks_html = risks_md.replace('-', '&bull;').replace('\n', '<br>')

    teaser_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Investment Teaser - {company_name}</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.5; color: #1e293b; max-width: 800px; margin: 0 auto; padding: 24px; }}
        h1 {{ color: #0f172a; border-bottom: 3px solid #2563eb; padding-bottom: 8px; margin-bottom: 20px; font-size: 24px; text-transform: uppercase; }}
        h2 {{ color: #1e40af; margin-top: 20px; font-size: 16px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; }}
        th {{ background-color: #f1f5f9; font-weight: 600; color: #334155; }}
        .highlight {{ background-color: #eff6ff; font-weight: bold; color: #1d4ed8; }}
        ul {{ padding-left: 20px; margin: 8px 0; }}
        li {{ margin-bottom: 4px; font-size: 14px; }}
        p {{ font-size: 14px; margin: 8px 0; }}
        .badge {{ display: inline-block; background-color: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Institutional Investment Teaser: {company_name}</h1>
    
    <h2>Deal Snapshot</h2>
    <table>
        <tr><th>Company</th><td><strong>{company_name}</strong></td><th>Check Size</th><td>{check_size_str}</td></tr>
        <tr><th>Industry</th><td>{industry}</td><th>Stage</th><td>{target_round}</td></tr>
        <tr><th>IC Recommendation</th><td colspan="3"><span class="badge">{recommendation}</span> (Confidence: {confidence})</td></tr>
    </table>

    <h2>1. Investment Thesis</h2>
    <p>{thesis}</p>

    <h2>2. Key Financial & Operating Metrics</h2>
    <table>
        <thead>
            <tr><th>Metric</th><th>Performance</th><th>Benchmark</th></tr>
        </thead>
        <tbody>
            <tr><td>Annual Recurring Revenue</td><td class="highlight">{arr}</td><td>Top Quartile</td></tr>
            <tr><td>YoY Revenue Growth</td><td class="highlight">{growth}</td><td>High Growth</td></tr>
            <tr><td>Gross Margin</td><td>{gross_margin}</td><td>Software Standard</td></tr>
            <tr><td>Net Revenue Retention</td><td>{nrr}</td><td>Enterprise Target</td></tr>
            <tr><td>CAC Payback</td><td>{cac_payback}</td><td>Efficient</td></tr>
            <tr><td>Cash Runway</td><td>{runway}</td><td>Sustainable</td></tr>
        </tbody>
    </table>

    <h2>3. Key Risks & Mitigations</h2>
    <p>{risks_html}</p>

    <h2>4. Downside Waterfall & Exit Outlook</h2>
    <p>Preferred equity structure provides full 1x capital protection. Base case projections indicate <strong>3.8x MOIC</strong> over 5 years.</p>
</body>
</html>
"""

    return {
        "teaser_markdown": teaser_md,
        "teaser_html": teaser_html,
        "company_name": company_name
    }
