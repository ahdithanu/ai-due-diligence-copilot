from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.domain.schemas import RAGQueryRequest, RAGQueryResponse
from backend.services.vector_rag_service import vector_rag_service

router = APIRouter(prefix="/investments", tags=["Vector RAG"])


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
