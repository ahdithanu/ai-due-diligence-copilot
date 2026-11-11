import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from backend.domain.schemas import OperationalKnowledgeItem

DEFAULT_KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    {
        "id": "kb-001",
        "title": "Valuation Multiple & Underwriting Hurdle Benchmarks",
        "category": "VALUATION_BENCHMARKS",
        "content_markdown": """# SaaS Valuation Multiples & Hurdle Guidelines
* **Target ARR Band ($5M - $25M)**:
  * Top-Quartile Growth (>40% YoY): 10.0x - 14.5x ARR
  * Median Growth (20% - 40% YoY): 7.5x - 10.0x ARR
  * Rule of 40 Benchmark: Growth Rate (%) + EBITDA Margin (%). Must exceed 40.0% for Series A lead check.
* **Underwriting Return Targets**:
  * Minimum Target MOIC: 3.0x on base case; 1.5x on downside stress scenario.
  * Minimum Target Net IRR: 25.0% over 5-year investment horizon.
""",
        "last_edited_by": "Investment Committee Lead",
        "citations_count": 18,
    },
    {
        "id": "kb-002",
        "title": "ASC 606 SaaS Recurring Revenue Recognition Standard",
        "category": "REVENUE_RECOGNITION_ASC606",
        "content_markdown": """# ASC 606 Revenue Recognition Invariants
* **Strict Recurring Revenue Exclusions**:
  * One-off implementation, onboarding, or training fees must be amortized or excluded from annualized recurring revenue (ARR).
  * Usage-based overages must display at least 3 consecutive quarters of stable consumption history to qualify for ARR treatment.
* **Gross Margin Floor**:
  * Enterprise Software gross margins must exceed 75.0% post-hosting and Tier-1 customer support allocation.
""",
        "last_edited_by": "Head of Financial QoE",
        "citations_count": 24,
    },
    {
        "id": "kb-003",
        "title": "IRS Section 1202 Qualified Small Business Stock (QSBS) Playbook",
        "category": "TAX_QSBS_RULES",
        "content_markdown": """# QSBS Federal Tax Shield Qualification
* **Section 1202 Criteria**:
  * Must be a domestic Delaware C-Corporation at share issuance.
  * Gross aggregate assets must not exceed $50,000,000 immediately before and after financing.
  * 80% of assets must be used in active conduct of qualified technology business.
* **LP Financial Benefit**:
  * Up to $10,000,000 or 10x adjusted basis in federal capital gains exemption per limited partner upon 5-year holding.
""",
        "last_edited_by": "Tax & Structuring Partner",
        "citations_count": 12,
    },
    {
        "id": "kb-004",
        "title": "Institutional Liquidation Preference & Anti-Dilution Covenants",
        "category": "DEAL_GOVERNANCE",
        "content_markdown": """# Liquidation Preference & Governance Standards
* **Preferred Stock Waterfall**:
  * Default stance: 1.0x Non-Participating Preferred with standard broad-based weighted average anti-dilution.
  * Reject participating preferred features or multi-tier liquidation ratchets (>1x) unless entry multiple is deeply discounted (>35% below peer median).
* **Protective Provisions**:
  * Series A preferred director consent required for indebtedness > $1,000,000 and equity issuances senior to Series A.
""",
        "last_edited_by": "General Counsel",
        "citations_count": 31,
    },
]


class OperationalKnowledgeService:
    """
    Arca Chapter 16: Operational Knowledge Base as a First-Class Product UI Feature.
    Underwriting standards, valuation rules, and legal invariants curated by human experts
    that agents strictly cite and adhere to.
    """

    def __init__(self):
        now_str = datetime.now(timezone.utc).isoformat()
        self._items: Dict[str, OperationalKnowledgeItem] = {
            item["id"]: OperationalKnowledgeItem(
                id=item["id"],
                title=item["title"],
                category=item["category"],
                content_markdown=item["content_markdown"],
                last_edited_by=item["last_edited_by"],
                updated_at=now_str,
                citations_count=item["citations_count"],
            )
            for item in DEFAULT_KNOWLEDGE_BASE
        }

    def list_knowledge_items(self) -> List[OperationalKnowledgeItem]:
        return list(self._items.values())

    def update_knowledge_item(
        self, item_id: str, title: str, content_markdown: str, editor: str = "Deal Lead"
    ) -> Optional[OperationalKnowledgeItem]:
        if item_id in self._items:
            now_str = datetime.now(timezone.utc).isoformat()
            item = self._items[item_id]
            item.title = title
            item.content_markdown = content_markdown
            item.last_edited_by = editor
            item.updated_at = now_str
            item.citations_count += 1
            return item
        return None


operational_knowledge_service = OperationalKnowledgeService()
