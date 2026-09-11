import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.db.models import (
    InvestmentModel,
    DocumentModel,
    DocumentChunkModel,
    EvidenceRecordModel
)
from backend.domain.schemas import (
    DiligenceStatus,
    DocumentType,
    ClaimType,
    DiligenceState,
    DocumentChunk
)
from backend.services.evidence_extractor import EvidenceExtractorService

DEMO_DEALS = [
    {
        "name": "Acme AI Systems",
        "industry": "Enterprise AI Automation",
        "target_round": "Series A",
        "check_size_usd": 5000000.0,
        "doc_filename": "acme_ai_pitch_deck.txt",
        "doc_content": (
            "Acme AI Systems Pitch Deck & Financial Materials\n"
            "Executive Summary: Acme AI delivers autonomous enterprise workflow orchestration.\n"
            "Market: TAM is $45B growing at 28% CAGR driven by global AI adoption.\n"
            "Financials: FY2024 ARR reached $10M with 80% Gross Margin and 125% Net Revenue Retention (NRR).\n"
            "Unit Economics: LTV/CAC ratio is 4.2x with 9 months CAC Payback period.\n"
            "Technology & Moat: 3 filed patents on workflow orchestration and fine-tuned model weights.\n"
            "Risks: Key person dependency on founding CTO. High customer concentration with top client representing 35% of ARR."
        )
    },
    {
        "name": "Nexus Quantum Inc",
        "industry": "Quantum Computing & Security",
        "target_round": "Seed",
        "check_size_usd": 2500000.0,
        "doc_filename": "nexus_quantum_deck.txt",
        "doc_content": (
            "Nexus Quantum Inc Executive Brief & Financial Model\n"
            "Company Overview: Next-generation fault-tolerant quantum encryption hardware.\n"
            "Market Opportunity: Post-quantum cryptography market expected to reach $15B by 2030.\n"
            "Financial Performance: Q4 2024 MRR reached $200K ($2.4M ARR) with 75% Gross Margin.\n"
            "Burn & Runway: Cash balance is $4M with a monthly burn rate of $250K (16 months runway).\n"
            "Competitive Landscape: Outperforming legacy HSM providers on key throughput metrics.\n"
            "Key Risks: Long enterprise sales cycles and hardware supply chain lead times."
        )
    },
    {
        "name": "Starlight Robotics",
        "industry": "Autonomous Logistics & Robotics",
        "target_round": "Series B",
        "check_size_usd": 12000000.0,
        "doc_filename": "starlight_robotics_materials.txt",
        "doc_content": (
            "Starlight Robotics Due Diligence Vault\n"
            "Product: Autonomous mobile robots (AMRs) for warehouse fulfillment.\n"
            "Market Size: Warehouse automation market is $35B expanding at 18% CAGR.\n"
            "Financial Highlights: FY2024 Revenue was $18M with 65% Gross Margin and Rule of 40 score of 48%.\n"
            "Unit Economics: CAC is $45K with ACV of $120K yielding 120% NRR across 85 active enterprise deployments.\n"
            "Moat: Proprietary SLAM navigation algorithms and hardware-software integration patents.\n"
            "Risk Factors: Supply chain component availability and regulatory safety standards."
        )
    }
]

extractor_service = EvidenceExtractorService()

async def init_seed_investments_if_empty(db: AsyncSession):
    """
    Checks if database has any existing investments.
    If 0, seeds 3 realistic institutional demo investment workspaces
    with documents, chunks, and extracted evidence.
    """
    res = await db.execute(select(func.count(InvestmentModel.id)))
    count = res.scalar_one_or_none() or 0
    if count > 0:
        return

    for deal in DEMO_DEALS:
        inv_id = str(uuid.uuid4())
        initial_state = DiligenceState(
            investment_id=inv_id,
            company_name=deal["name"],
            industry=deal["industry"],
            target_round=deal["target_round"],
            check_size_usd=deal["check_size_usd"],
            status=DiligenceStatus.CREATED,
            deployment_id="growth_saas_default"
        )

        db_inv = InvestmentModel(
            id=inv_id,
            company_name=deal["name"],
            industry=deal["industry"],
            target_round=deal["target_round"],
            check_size_usd=deal["check_size_usd"],
            status=DiligenceStatus.CREATED.value,
            state_snapshot_json=initial_state.model_dump(mode="json")
        )
        db.add(db_inv)
        await db.flush()

        # Add document
        doc_id = str(uuid.uuid4())
        content_text = deal["doc_content"]
        db_doc = DocumentModel(
            id=doc_id,
            investment_id=inv_id,
            filename=deal["doc_filename"],
            file_type="txt",
            file_size=len(content_text.encode("utf-8")),
            storage_path=f"storage/uploads/{doc_id}_{deal['doc_filename']}",
            doc_type=DocumentType.PITCH_DECK.value
        )
        db.add(db_doc)
        await db.flush()

        # Add document chunk
        chunk_id = str(uuid.uuid4())
        chunk_obj = DocumentChunk(
            id=chunk_id,
            document_id=doc_id,
            chunk_index=0,
            page_number=1,
            section_title="Executive Summary & Financials",
            content=content_text,
            char_count=len(content_text)
        )
        db_chunk = DocumentChunkModel(
            id=chunk_obj.id,
            document_id=doc_id,
            chunk_index=chunk_obj.chunk_index,
            page_number=chunk_obj.page_number,
            section_title=chunk_obj.section_title,
            content=chunk_obj.content,
            char_count=chunk_obj.char_count
        )
        db.add(db_chunk)
        await db.flush()

        # Extract & save evidence
        raw_evidence = extractor_service.extract_evidence([chunk_obj])
        for ev in raw_evidence:
            db_ev = EvidenceRecordModel(
                id=ev.id,
                investment_id=inv_id,
                document_id=doc_id,
                chunk_id=chunk_id,
                content=ev.content,
                page_number=ev.page_number,
                section_title=ev.section_title,
                confidence=ev.confidence,
                claim_type=ev.claim_type.value,
                metadata_json=ev.metadata
            )
            db.add(db_ev)

    await db.commit()
