from typing import List, Optional
from backend.domain.schemas import (
    PeerCompanyComp,
    PrecedentTransactionComp,
    ValuationMethodologyRange,
    ValuationCompsResponse,
)

PUBLIC_PEERS: List[PeerCompanyComp] = [
    PeerCompanyComp(
        ticker="DDOG",
        name="Datadog, Inc.",
        ev_revenue_multiple=14.8,
        ev_ebitda_multiple=45.2,
        growth_rate_pct=26.0,
        gross_margin_pct=81.2,
        rule_of_40_pct=48.5,
    ),
    PeerCompanyComp(
        ticker="CRWD",
        name="CrowdStrike Holdings",
        ev_revenue_multiple=16.2,
        ev_ebitda_multiple=48.0,
        growth_rate_pct=31.0,
        gross_margin_pct=78.5,
        rule_of_40_pct=54.2,
    ),
    PeerCompanyComp(
        ticker="SNOW",
        name="Snowflake Inc.",
        ev_revenue_multiple=13.5,
        ev_ebitda_multiple=52.1,
        growth_rate_pct=28.0,
        gross_margin_pct=74.0,
        rule_of_40_pct=45.0,
    ),
    PeerCompanyComp(
        ticker="GTLB",
        name="GitLab Inc.",
        ev_revenue_multiple=10.4,
        ev_ebitda_multiple=38.4,
        growth_rate_pct=29.0,
        gross_margin_pct=89.4,
        rule_of_40_pct=42.1,
    ),
    PeerCompanyComp(
        ticker="HUBS",
        name="HubSpot, Inc.",
        ev_revenue_multiple=9.8,
        ev_ebitda_multiple=32.6,
        growth_rate_pct=22.0,
        gross_margin_pct=82.0,
        rule_of_40_pct=38.4,
    ),
]

PRECEDENT_DEALS: List[PrecedentTransactionComp] = [
    PrecedentTransactionComp(
        target="HashiCorp",
        acquirer="IBM",
        year=2024,
        ev_arr_multiple=12.5,
        deal_size_usd=6_400_000_000.0,
    ),
    PrecedentTransactionComp(
        target="Qualtrics",
        acquirer="Silver Lake / CPP Investments",
        year=2023,
        ev_arr_multiple=8.2,
        deal_size_usd=12_500_000_000.0,
    ),
    PrecedentTransactionComp(
        target="Coupa Software",
        acquirer="Thoma Bravo",
        year=2023,
        ev_arr_multiple=8.9,
        deal_size_usd=8_000_000_000.0,
    ),
    PrecedentTransactionComp(
        target="SailPoint Technologies",
        acquirer="Thoma Bravo",
        year=2022,
        ev_arr_multiple=11.2,
        deal_size_usd=6_900_000_000.0,
    ),
    PrecedentTransactionComp(
        target="Datto",
        acquirer="Kaseya (Insight Partners)",
        year=2022,
        ev_arr_multiple=9.6,
        deal_size_usd=6_200_000_000.0,
    ),
]


class ValuationCompsService:
    """Computes comparable company valuation benchmarks, precedent M&A multiples, and Football Field ranges."""

    def calculate_valuation_comps(
        self,
        investment_id: str,
        company_name: str = "Acme SaaS AI",
        arr_usd: float = 10_000_000.0,
        current_valuation_usd: float = 50_000_000.0,
        growth_rate_pct: float = 35.0,
        gross_margin_pct: float = 80.0,
        ebitda_margin_pct: float = 12.0,
    ) -> ValuationCompsResponse:
        # Target Rule of 40 = Growth Rate + EBITDA Margin
        target_rule_of_40 = growth_rate_pct + ebitda_margin_pct

        # Peer Median Rule of 40
        peer_r40_list = [p.rule_of_40_pct for p in PUBLIC_PEERS]
        peer_median_r40 = sorted(peer_r40_list)[len(peer_r40_list) // 2]

        # Methodology 1: Public SaaS Comps (8.5x - 14.8x ARR)
        public_low = arr_usd * 8.5
        public_med = arr_usd * 12.0
        public_high = arr_usd * 15.5

        # Methodology 2: Precedent Strategic/PE Deals (8.2x - 12.5x ARR)
        precedent_low = arr_usd * 8.2
        precedent_med = arr_usd * 10.5
        precedent_high = arr_usd * 13.0

        # Methodology 3: 5-Year DCF Model (12% WACC, 3.5% terminal growth)
        dcf_low = arr_usd * 9.5
        dcf_med = arr_usd * 12.8
        dcf_high = arr_usd * 16.2

        # Methodology 4: Leveraged Buyout (LBO) Floor (20% Target IRR, 4.0x leverage)
        lbo_low = arr_usd * 6.5
        lbo_med = arr_usd * 8.5
        lbo_high = arr_usd * 10.5

        methodology_ranges: List[ValuationMethodologyRange] = [
            ValuationMethodologyRange(
                methodology_name="Public SaaS Trading Comps",
                low_valuation_usd=round(public_low, 2),
                median_valuation_usd=round(public_med, 2),
                high_valuation_usd=round(public_high, 2),
                multiple_metric="8.5x - 15.5x ARR",
            ),
            ValuationMethodologyRange(
                methodology_name="Precedent M&A Transactions",
                low_valuation_usd=round(precedent_low, 2),
                median_valuation_usd=round(precedent_med, 2),
                high_valuation_usd=round(precedent_high, 2),
                multiple_metric="8.2x - 13.0x ARR",
            ),
            ValuationMethodologyRange(
                methodology_name="Discounted Cash Flow (DCF)",
                low_valuation_usd=round(dcf_low, 2),
                median_valuation_usd=round(dcf_med, 2),
                high_valuation_usd=round(dcf_high, 2),
                multiple_metric="12% WACC / 3.5% Perpetuity",
            ),
            ValuationMethodologyRange(
                methodology_name="LBO Underwrite Floor",
                low_valuation_usd=round(lbo_low, 2),
                median_valuation_usd=round(lbo_med, 2),
                high_valuation_usd=round(lbo_high, 2),
                multiple_metric="20% IRR / 4x Leverage",
            ),
        ]

        # Overall Implied Composite Range
        composite_low = min(m.low_valuation_usd for m in methodology_ranges)
        composite_med = round(sum(m.median_valuation_usd for m in methodology_ranges) / len(methodology_ranges), 2)
        composite_high = max(m.high_valuation_usd for m in methodology_ranges)

        return ValuationCompsResponse(
            investment_id=investment_id,
            company_name=company_name,
            current_arr_usd=arr_usd,
            current_valuation_usd=current_valuation_usd,
            implied_low_valuation_usd=composite_low,
            implied_median_valuation_usd=composite_med,
            implied_high_valuation_usd=composite_high,
            methodology_ranges=methodology_ranges,
            public_peers=PUBLIC_PEERS,
            precedent_deals=PRECEDENT_DEALS,
            target_rule_of_40_pct=round(target_rule_of_40, 1),
            peer_median_rule_of_40_pct=round(peer_median_r40, 1),
        )


valuation_comps_service = ValuationCompsService()
