import pytest
from datetime import datetime
from backend.domain.schemas import (
    ClaimType, MaterialityLevel, DiligenceStatus, DocumentType,
    EvidenceRecord, FinancialMetricRecord, ClaimNode, DiligenceState
)

def test_claim_type_enum():
    assert ClaimType.FACT == "FACT"
    assert ClaimType.CALCULATION == "CALCULATION"
    assert ClaimType.INFERENCE == "INFERENCE"
    assert ClaimType.ASSUMPTION == "ASSUMPTION"
    assert ClaimType.UNRESOLVED_QUESTION == "UNRESOLVED_QUESTION"

def test_evidence_record_creation():
    record = EvidenceRecord(
        document_id="doc_123",
        chunk_id="chunk_456",
        content="Company ARR is $10M in FY2024.",
        claim_type=ClaimType.FACT,
        page_number=2,
        section_title="Financial Highlights"
    )
    assert record.document_id == "doc_123"
    assert record.claim_type == ClaimType.FACT
    assert record.page_number == 2
    assert record.confidence == 1.0

def test_financial_metric_record():
    metric = FinancialMetricRecord(
        metric_name="ARR",
        value=10000000.0,
        unit="USD",
        period="FY2024",
        formula="MRR * 12",
        input_evidence_ids=["ev_1"]
    )
    assert metric.value == 10000000.0
    assert metric.is_deterministic is True

def test_diligence_state_serialization():
    state = DiligenceState(
        investment_id="inv_001",
        company_name="Acme AI",
        industry="Enterprise Software",
        target_round="Series A",
        check_size_usd=5000000.0
    )
    serialized = state.model_dump(mode="json")
    assert serialized["investment_id"] == "inv_001"
    assert serialized["status"] == "CREATED"

    deserialized = DiligenceState.model_validate(serialized)
    assert deserialized.company_name == "Acme AI"
    assert deserialized.check_size_usd == 5000000.0
