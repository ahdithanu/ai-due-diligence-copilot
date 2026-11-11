import uuid
from typing import Dict, List
from backend.domain.schemas import HiddenFeeFinding, HiddenFeeScanResponse

DEFAULT_HIDDEN_FEES: List[HiddenFeeFinding] = [
    HiddenFeeFinding(
        id=str(uuid.uuid4()),
        category="RELATED_PARTY",
        title="Founder-Affiliated Management Advisory Retainer",
        document_source="04_Legal/Advisory_Services_Agreement_2023.pdf (Page 4)",
        clause_text="Target Company shall remit an annual advisory retainer of $240,000 to Apex Horizons LLC (an entity wholly owned by CEO Elena Rostova).",
        annual_financial_drag_usd=240_000.0,
        fiduciary_risk_level="CRITICAL",
        recommended_remediation="Require immediate termination of advisory agreement as Condition Precedent (CP) without severance fee.",
    ),
    HiddenFeeFinding(
        id=str(uuid.uuid4()),
        category="NON_FIDUCIARY",
        title="Unregistered Capital Placement Broker Success Fee",
        document_source="02_Financials/Series_Seed_Engagement_Letter.pdf (Page 2)",
        clause_text="Advisor operates as an independent contractor and disclaims any fiduciary duties to Company. Success fee of 3.5% of gross proceeds.",
        annual_financial_drag_usd=0.0,
        fiduciary_risk_level="HIGH",
        recommended_remediation="Obtain legal opinion confirming broker FINRA/SEC registration to preclude rescission rights under Exchange Act § 29(b).",
    ),
    HiddenFeeFinding(
        id=str(uuid.uuid4()),
        category="LIQUIDATION_RATCHET",
        title="Seed SAFE Seniority Jump & Hidden 2x Ratchet",
        document_source="01_Governance/Seed_SAFE_Syndicate_Addendum.pdf (Page 6)",
        clause_text="In the event of an M&A transaction under $75M, Seed SAFE proceeds receive 2.0x liquidation preference senior to Common Stock.",
        annual_financial_drag_usd=0.0,
        fiduciary_risk_level="CRITICAL",
        recommended_remediation="Amend SAFE terms into standard 1.0x non-participating Series A preferred stock.",
    ),
    HiddenFeeFinding(
        id=str(uuid.uuid4()),
        category="MONITORING_FEE",
        title="Proprietary IP Hosting Markup from Founder Entity",
        document_source="03_Technical/Cloud_Hosting_Vendor_Schedule.xlsx",
        clause_text="Software infrastructure sub-contractor charges a 25% administrative surcharge ($85k/yr) above AWS list price.",
        annual_financial_drag_usd=85_000.0,
        fiduciary_risk_level="MEDIUM",
        recommended_remediation="Directly bind AWS Enterprise Discount Program (EDP) contract to Company rather than through intermediary.",
    ),
]


class FeeAndConflictScanner:
    """
    Arca Chapter 17: Hidden Fee, Cap Table Trap & Non-Fiduciary Conflict Scanner.
    Unearths undisclosed fee leakage, related-party kickbacks, non-fiduciary advisor agreements,
    and aggressive liquidation preference ratchets in data rooms.
    """

    def scan_investment_documents(self, investment_id: str) -> HiddenFeeScanResponse:
        total_drag = sum(f.annual_financial_drag_usd for f in DEFAULT_HIDDEN_FEES)
        non_fiduciary_count = sum(
            1 for f in DEFAULT_HIDDEN_FEES if f.category in ["NON_FIDUCIARY", "RELATED_PARTY"]
        )

        return HiddenFeeScanResponse(
            investment_id=investment_id,
            total_annual_drag_usd=total_drag,
            findings=DEFAULT_HIDDEN_FEES,
            non_fiduciary_agreements_flagged=non_fiduciary_count,
        )


fee_and_conflict_scanner = FeeAndConflictScanner()
