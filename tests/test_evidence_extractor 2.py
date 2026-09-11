import pytest
from backend.domain.schemas import DocumentChunk, ClaimType
from backend.services.evidence_extractor import EvidenceExtractorService

def test_extract_financial_evidence():
    extractor = EvidenceExtractorService()
    chunk = DocumentChunk(
        document_id="doc_1",
        chunk_index=0,
        content="Revenue for FY2024 reached $15.5M with a Gross Margin of 85%. Burn Rate is $200K monthly."
    )
    records = extractor.extract_evidence([chunk])
    assert len(records) > 0
    
    financial_contents = [r.content for r in records if r.metadata.get("category") == "financial_metric"]
    assert any("Revenue" in c or "$15.5M" in c for c in financial_contents)

def test_classify_claim_types():
    extractor = EvidenceExtractorService()
    assert extractor._classify_claim_type("Revenue was $10M in FY2023.") == ClaimType.FACT
    assert extractor._classify_claim_type("We calculate total ARR as MRR * 12.") == ClaimType.CALCULATION
    assert extractor._classify_claim_type("We expect to reach 100 enterprise customers next year.") == ClaimType.ASSUMPTION
    assert extractor._classify_claim_type("Customer churn metrics remain unclear in Q3.") == ClaimType.UNRESOLVED_QUESTION
