import os
import re
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.db.database import get_db
from backend.db.models import InvestmentModel, DocumentModel, DocumentChunkModel, EvidenceRecordModel
from backend.domain.schemas import (
    CreateInvestmentRequest, InvestmentResponse, DiligenceState, DiligenceStatus,
    DocumentType, DocumentChunk, EvidenceRecord, ClaimType,
    DealComparisonItem, RedFlagAlert, KeyMetrics, MaterialityLevel,
    PortfolioComparisonResponse, CompanyComparisonSummary, RedFlagSeverity
)

from backend.services.document_parser import DocumentParserService
from backend.services.evidence_extractor import EvidenceExtractorService
from backend.services.memo_generator import generate_investment_memo_pdf, generate_investment_memo
from backend.services.benchmarking_service import generate_portfolio_comparison, detect_portfolio_red_flags



router = APIRouter(prefix="/investments", tags=["Investments"])

parser_service = DocumentParserService()
extractor_service = EvidenceExtractorService()

@router.post("", response_model=InvestmentResponse, status_code=status.HTTP_201_CREATED)
async def create_investment(
    req: CreateInvestmentRequest,
    db: AsyncSession = Depends(get_db)
):
    inv_id = str(uuid.uuid4())
    initial_state = DiligenceState(
        investment_id=inv_id,
        company_name=req.company_name,
        industry=req.industry,
        target_round=req.target_round,
        check_size_usd=req.check_size_usd,
        status=DiligenceStatus.CREATED
    )

    db_investment = InvestmentModel(
        id=inv_id,
        company_name=req.company_name,
        industry=req.industry,
        target_round=req.target_round,
        check_size_usd=req.check_size_usd,
        status=DiligenceStatus.CREATED.value,
        state_snapshot_json=initial_state.model_dump(mode="json")
    )
    db.add(db_investment)
    await db.commit()

    return InvestmentResponse(
        investment_id=inv_id,
        company_name=req.company_name,
        industry=req.industry,
        target_round=req.target_round,
        check_size_usd=req.check_size_usd,
        status=DiligenceStatus.CREATED,
        created_at=db_investment.created_at,
        document_count=0,
        evidence_count=0
    )

@router.get("", response_model=List[InvestmentResponse])
async def list_investments(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(InvestmentModel)
        .options(
            selectinload(InvestmentModel.documents),
            selectinload(InvestmentModel.evidence_records)
        )
        .order_by(InvestmentModel.created_at.desc())
    )
    result = await db.execute(stmt)
    investments = result.scalars().all()
    
    responses = []
    for inv in investments:
        doc_count = len(inv.documents) if inv.documents else 0
        ev_count = len(inv.evidence_records) if inv.evidence_records else 0
        responses.append(
            InvestmentResponse(
                investment_id=inv.id,
                company_name=inv.company_name,
                industry=inv.industry,
                target_round=inv.target_round,
                check_size_usd=inv.check_size_usd,
                status=DiligenceStatus(inv.status),
                created_at=inv.created_at,
                document_count=doc_count,
                evidence_count=ev_count
            )
        )
    return responses


@router.get("/{investment_id}", response_model=DiligenceState)
async def get_investment_state(investment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")
    
    if inv.state_snapshot_json:
        return DiligenceState.model_validate(inv.state_snapshot_json)
    
    return DiligenceState(
        investment_id=inv.id,
        company_name=inv.company_name,
        industry=inv.industry,
        target_round=inv.target_round,
        check_size_usd=inv.check_size_usd,
        status=DiligenceStatus(inv.status)
    )

@router.post("/{investment_id}/documents")
async def upload_document(
    investment_id: str,
    file: UploadFile = File(...),
    doc_type: str = Form("OTHER"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    # Create storage dir if not exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    doc_id = str(uuid.uuid4())
    filename = file.filename or "uploaded_document"
    file_ext = os.path.splitext(filename)[1]
    storage_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")

    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(storage_path)

    # 1. Parse document into chunks
    chunks = parser_service.parse_file(storage_path, doc_id)

    # 2. Extract evidence records
    evidence_records = extractor_service.extract_evidence(chunks)

    # Save to Database
    db_doc = DocumentModel(
        id=doc_id,
        investment_id=investment_id,
        filename=filename,
        file_type=file_ext,
        file_size=file_size,
        storage_path=storage_path,
        doc_type=doc_type
    )
    db.add(db_doc)

    for chunk in chunks:
        db_chunk = DocumentChunkModel(
            id=chunk.id,
            document_id=doc_id,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            section_title=chunk.section_title,
            content=chunk.content,
            char_count=chunk.char_count
        )
        db.add(db_chunk)

    for ev in evidence_records:
        db_ev = EvidenceRecordModel(
            id=ev.id,
            investment_id=investment_id,
            document_id=doc_id,
            chunk_id=ev.chunk_id,
            content=ev.content,
            page_number=ev.page_number,
            section_title=ev.section_title,
            extracted_at=ev.extracted_at,
            confidence=ev.confidence,
            claim_type=ev.claim_type.value,
            metadata_json=ev.metadata
        )
        db.add(db_ev)

    # Update State Snapshot
    state_dict = inv.state_snapshot_json or DiligenceState(
        investment_id=inv.id,
        company_name=inv.company_name,
        industry=inv.industry,
        target_round=inv.target_round
    ).model_dump(mode="json")
    
    current_state = DiligenceState.model_validate(state_dict)
    current_state.status = DiligenceStatus.EVIDENCE_EXTRACTED
    current_state.documents.append({
        "id": doc_id,
        "filename": filename,
        "file_type": file_ext,
        "file_size": file_size,
        "doc_type": doc_type
    })
    current_state.document_chunks.extend(chunks)
    current_state.evidence_records.extend(evidence_records)

    inv.status = DiligenceStatus.EVIDENCE_EXTRACTED.value
    inv.state_snapshot_json = current_state.model_dump(mode="json")

    await db.commit()

    return {
        "document_id": doc_id,
        "filename": filename,
        "chunks_extracted": len(chunks),
        "evidence_extracted": len(evidence_records),
        "status": DiligenceStatus.EVIDENCE_EXTRACTED
    }

from backend.db.models import InvestmentModel, DocumentModel, DocumentChunkModel, EvidenceRecordModel, FinancialMetricModel, InvestmentMemoModel
from backend.domain.schemas import (
    CreateInvestmentRequest, InvestmentResponse, DiligenceState, DiligenceStatus,
    DocumentType, DocumentChunk, EvidenceRecord, ClaimType, FinancialMetricRecord,
    InvestmentMemoResponse
)

@router.get("/{investment_id}/evidence", response_model=List[EvidenceRecord])
async def get_investment_evidence(investment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EvidenceRecordModel).where(EvidenceRecordModel.investment_id == investment_id))
    db_records = result.scalars().all()
    
    return [
        EvidenceRecord(
            id=rec.id,
            document_id=rec.document_id,
            chunk_id=rec.chunk_id,
            content=rec.content,
            page_number=rec.page_number,
            section_title=rec.section_title,
            extracted_at=rec.extracted_at,
            confidence=rec.confidence,
            claim_type=ClaimType(rec.claim_type),
            metadata=rec.metadata_json or {}
        )
        for rec in db_records
    ]

@router.get("/{investment_id}/financials", response_model=List[FinancialMetricRecord])
async def get_investment_financials(investment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    fm_result = await db.execute(select(FinancialMetricModel).where(FinancialMetricModel.investment_id == investment_id))
    db_fms = fm_result.scalars().all()

    if db_fms:
        return [
            FinancialMetricRecord(
                id=rec.id,
                metric_name=rec.metric_name,
                value=rec.value,
                unit=rec.unit,
                period=rec.period,
                formula=rec.formula,
                input_evidence_ids=rec.input_evidence_ids_json or [],
                is_deterministic=rec.is_deterministic,
                confidence=rec.confidence
            )
            for rec in db_fms
        ]
    
    if inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
        return state.financial_metrics

    return []


@router.get("/{investment_id}/memo", response_model=InvestmentMemoResponse)
async def get_investment_memo(investment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    memo_result = await db.execute(select(InvestmentMemoModel).where(InvestmentMemoModel.investment_id == investment_id))
    db_memo = memo_result.scalar_one_or_none()

    if db_memo:
        return InvestmentMemoResponse(
            id=db_memo.id,
            investment_id=db_memo.investment_id,
            memo_markdown=db_memo.memo_markdown,
            recommendation=db_memo.recommendation,
            confidence_score=db_memo.confidence_score,
            created_at=db_memo.created_at
        )

    # Fallback to state snapshot if present
    if inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
        if state.memo_markdown:
            return InvestmentMemoResponse(
                id=str(uuid.uuid4()),
                investment_id=state.investment_id,
                memo_markdown=state.memo_markdown,
                recommendation=state.recommendation or "PASS",
                confidence_score=state.confidence_score or 0.0,
                created_at=inv.updated_at
            )

    raise HTTPException(status_code=404, detail="Investment memo not found for this investment")


@router.get("/{investment_id}/memo/download")
async def download_investment_memo(
    investment_id: str,
    format: str = "pdf",
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(InvestmentModel).where(InvestmentModel.id == investment_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment workspace not found")

    memo_text = None
    memo_result = await db.execute(select(InvestmentMemoModel).where(InvestmentMemoModel.investment_id == investment_id))
    db_memo = memo_result.scalar_one_or_none()
    if db_memo and db_memo.memo_markdown:
        memo_text = db_memo.memo_markdown

    if not memo_text and inv.state_snapshot_json:
        state = DiligenceState.model_validate(inv.state_snapshot_json)
        if state.memo_markdown:
            memo_text = state.memo_markdown
        else:
            memo_text = generate_investment_memo(state)

    if not memo_text:
        raise HTTPException(status_code=404, detail="Investment memo not found for this investment")

    company_name = (inv.company_name or "Company").replace(" ", "_")
    fmt = format.lower()

    if fmt == "pdf":
        pdf_bytes = generate_investment_memo_pdf(memo_text, inv.company_name or "Company")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={company_name}_Investment_Memo.pdf"}
        )
    elif fmt in ("markdown", "md"):
        return Response(
            content=memo_text,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={company_name}_Investment_Memo.md"}
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{format}'. Supported formats are 'pdf' and 'markdown'.")


@router.get("/compare", response_model=PortfolioComparisonResponse)
async def compare_investments(
    ids: Optional[str] = Query(None, description="Comma-separated investment IDs to compare"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(InvestmentModel).order_by(InvestmentModel.created_at.desc())
    result = await db.execute(stmt)
    investments = result.scalars().all()

    target_ids = set(ids.split(",")) if ids else None

    states: List[DiligenceState] = []
    for inv in investments:
        if target_ids and inv.id not in target_ids:
            continue

        state = None
        if inv.state_snapshot_json:
            try:
                state = DiligenceState.model_validate(inv.state_snapshot_json)
            except Exception:
                pass

        if not state:
            state = DiligenceState(
                investment_id=inv.id,
                company_name=inv.company_name,
                industry=inv.industry,
                target_round=inv.target_round,
                check_size_usd=inv.check_size_usd,
                status=DiligenceStatus(inv.status)
            )

        states.append(state)

    return generate_portfolio_comparison(states)


@router.get("/red-flags", response_model=List[RedFlagAlert])
async def get_red_flag_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(InvestmentModel)
    result = await db.execute(stmt)
    investments = result.scalars().all()

    states: List[DiligenceState] = []
    for inv in investments:
        state = None
        if inv.state_snapshot_json:
            try:
                state = DiligenceState.model_validate(inv.state_snapshot_json)
            except Exception:
                pass

        if not state:
            state = DiligenceState(
                investment_id=inv.id,
                company_name=inv.company_name,
                industry=inv.industry,
                target_round=inv.target_round,
                check_size_usd=inv.check_size_usd,
                status=DiligenceStatus(inv.status)
            )

        states.append(state)

    alerts = detect_portfolio_red_flags(states)

    if severity:
        sev_upper = severity.upper()
        alerts = [
            a for a in alerts
            if a.severity.value.upper() == sev_upper or a.severity.name.upper() == sev_upper or a.materiality.value.upper() == sev_upper
        ]

    return alerts





