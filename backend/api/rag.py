from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.domain.schemas import (
    RAGQueryRequest,
    RAGQueryResponse,
    TwoStageRAGRequest,
    TwoStageRAGResult,
    TenantContext,
    UserRole
)
from backend.services.vector_rag_service import vector_rag_service

router = APIRouter(prefix="/investments", tags=["Vector RAG"])


@router.post("/{investment_id}/rag/two-stage-search", response_model=TwoStageRAGResult)
async def two_stage_rag_search(
    investment_id: str,
    request: TwoStageRAGRequest
) -> TwoStageRAGResult:
    """
    Executes an enterprise Two-Stage RAG retrieval:
    1. Pre-retrieval Multi-Tenant Isolation and RBAC role clearance.
    2. Stage 1 Broad Candidate Retrieval (candidate_k, default 20).
    3. Stage 2 Reciprocal Rank Fusion (RRF) & Hierarchical Context Expansion.
    4. Groundedness Gate & Hallucination Abstention.
    """
    try:
        tenant_context = None
        if request.org_id:
            role = request.role or UserRole.DEAL_LEAD
            tenant_context = TenantContext(
                org_id=request.org_id,
                org_name="Caller Org",
                user_id="user_rag_caller",
                user_email="caller@firm.com",
                role=role
            )

        result = vector_rag_service.two_stage_rag_search(
            investment_id=investment_id,
            query=request.query,
            tenant_context=tenant_context,
            candidate_k=request.candidate_k,
            final_top_k=request.final_top_k,
            groundedness_threshold=request.groundedness_threshold
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute two-stage RAG search: {str(e)}"
        )


@router.post("/{investment_id}/rag/search", response_model=RAGQueryResponse)
async def search_rag(
    investment_id: str,
    request: RAGQueryRequest
):
    """
    Executes hybrid vector + keyword search over workspace document chunks.
    Calculates hybrid score as 0.7 * Cosine + 0.3 * Keyword.
    """
    try:
        response = vector_rag_service.hybrid_search(
            investment_id=investment_id,
            query=request.query,
            top_k=request.top_k,
            min_hybrid_score=request.min_hybrid_score
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute vector RAG search: {str(e)}"
        )


@router.post("/{investment_id}/rag/reindex")
async def reindex_rag(
    investment_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Re-indexes all workspace document chunks into the vector store.
    """
    try:
        count = await vector_rag_service.reindex_workspace(investment_id, db)
        return {
            "status": "success",
            "investment_id": investment_id,
            "indexed_chunks": count,
            "message": f"Successfully re-indexed {count} document chunks into vector store."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-index vector store: {str(e)}"
        )
