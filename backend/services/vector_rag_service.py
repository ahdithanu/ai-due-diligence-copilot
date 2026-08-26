import math
import hashlib
import time
import uuid
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.domain.schemas import RAGSearchResult, RAGQueryRequest, RAGQueryResponse
from backend.db.models import DocumentChunkModel, DocumentModel


EMBEDDING_DIM = 384

DEFAULT_WORKSPACE_CHUNKS = [
    {
        "id": "rag-chunk-1",
        "document_name": "Series_A_Pitch_Deck.pdf",
        "page_number": 14,
        "section_title": "Financial Highlights & ARR Breakdown",
        "snippet": "Annual Recurring Revenue (ARR) reached $12.4M in Q3 2025, representing a 145% YoY growth rate. Gross margins expanded to 78%, driven by automated cloud infrastructure optimization and expanding enterprise deal sizes.",
        "metadata": {"author": "CFO", "created_at": "2025-10-15"}
    },
    {
        "id": "rag-chunk-2",
        "document_name": "Financial_Model_v3.xlsx",
        "page_number": 3,
        "section_title": "Unit Economics & CAC Sensitivity",
        "snippet": "LTV/CAC ratio stands at 4.2x with a payback period of 11.5 months. Net Revenue Retention (NRR) is 128% across enterprise cohorts, demonstrating strong expansion motion within Fortune 500 accounts.",
        "metadata": {"tab": "Cohort Analysis"}
    },
    {
        "id": "rag-chunk-3",
        "document_name": "Cap_Table_Legal_Agreement.pdf",
        "page_number": 22,
        "section_title": "Liquidation Preference & Seniority",
        "snippet": "Series A Preferred Shareholders hold a 1x non-participating liquidation preference with a senior liquidation rank over Common Stock. Convertible notes automatically converted into Series A at a 20% discount rate.",
        "metadata": {"clause": "Section 4.1 Liquidation"}
    },
    {
        "id": "rag-chunk-4",
        "document_name": "Customer_Due_Diligence_Report.pdf",
        "page_number": 8,
        "section_title": "Customer Concentration Risk",
        "snippet": "Top 5 customers account for 34% of total ARR. Customer A represents 12% of revenue with contract renewal scheduled for Q2 2026. Churn rate remains below 1.2% annualized.",
        "metadata": {"risk_level": "MEDIUM"}
    },
    {
        "id": "rag-chunk-5",
        "document_name": "Technical_Architecture_Audit.pdf",
        "page_number": 5,
        "section_title": "Security Compliance & SOC2 Type II",
        "snippet": "The application architecture implements end-to-end encryption at rest and in transit (AES-256 and TLS 1.3). SOC2 Type II compliance audit completed with zero non-conformances reported.",
        "metadata": {"auditor": "Deloitte Tech"}
    },
    {
        "id": "rag-chunk-6",
        "document_name": "Market_Expansion_Strategy.pdf",
        "page_number": 19,
        "section_title": "TAM & Competitive Moat",
        "snippet": "Total Addressable Market (TAM) is estimated at $45B globally. Proprietary AI vector routing and automated due diligence graph workflows present a 2-year technical lead over legacy manual audit solutions.",
        "metadata": {"region": "Global"}
    }
]


def normalize_vector(vec: List[float]) -> List[float]:
    """
    L2-normalizes a float vector so sum(v^2) == 1.0.
    """
    squared_sum = sum(v * v for v in vec)
    if squared_sum <= 0:
        val = 1.0 / math.sqrt(len(vec))
        return [val] * len(vec)
    magnitude = math.sqrt(squared_sum)
    return [v / magnitude for v in vec]


def generate_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Generates a deterministic, normalized 384-dimensional embedding vector for given text.
    Uses SHA-256 feature hashing across tokens and subwords.
    """
    vec = [0.0] * dim
    if not text or not text.strip():
        val = 1.0 / math.sqrt(dim)
        return [val] * dim

    words = re.findall(r'\w+', text.lower())
    
    # Hash whole words and subword character trigrams
    features = list(words)
    for word in words:
        if len(word) >= 3:
            for i in range(len(word) - 2):
                features.append(word[i:i+3])

    for feat in features:
        h = hashlib.sha256(feat.encode('utf-8')).digest()
        # Extract 16 two-byte integers to distribute weight across dimensions
        for i in range(0, len(h), 2):
            val = (h[i] << 8) | h[i+1]
            idx = val % dim
            sign = 1.0 if (val & 0x8000) else -1.0
            vec[idx] += sign

    return normalize_vector(vec)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Computes cosine similarity between two L2-normalized vectors.
    Since both vectors are unit vectors, dot product equals cosine similarity.
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vector dimension mismatch: {len(vec1)} vs {len(vec2)}")
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    # Clamp to [0.0, 1.0] range for similarity score usage
    return max(0.0, min(1.0, dot_product))


def compute_keyword_score(query: str, snippet: str) -> float:
    """
    Calculates a keyword overlap score between 0.0 and 1.0.
    """
    stopwords = {"the", "a", "an", "is", "are", "of", "and", "or", "in", "to", "for", "with", "on", "at", "by", "from", "it", "this", "that"}
    query_words = [w for w in re.findall(r'\w+', query.lower()) if w not in stopwords]
    if not query_words:
        query_words = re.findall(r'\w+', query.lower())
    
    if not query_words:
        return 0.0

    snippet_lower = snippet.lower()
    snippet_words = set(re.findall(r'\w+', snippet_lower))

    matches = sum(1 for w in query_words if w in snippet_words)
    overlap_score = matches / len(query_words)

    # Exact phrase bonus
    if query.strip().lower() in snippet_lower:
        overlap_score = min(1.0, overlap_score + 0.25)

    return max(0.0, min(1.0, overlap_score))


class IndexedChunk:
    def __init__(
        self,
        id: str,
        document_name: str,
        snippet: str,
        page_number: Optional[int] = None,
        section_title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ):
        self.id = id
        self.document_name = document_name
        self.snippet = snippet
        self.page_number = page_number
        self.section_title = section_title
        self.metadata = metadata or {}
        self.embedding = embedding or generate_embedding(snippet)


class VectorRAGService:
    def __init__(self):
        # Maps investment_id -> List[IndexedChunk]
        self._vector_store: Dict[str, List[IndexedChunk]] = {}

    def _ensure_indexed(self, investment_id: str):
        if investment_id not in self._vector_store or not self._vector_store[investment_id]:
            self.seed_default_workspace(investment_id)

    def seed_default_workspace(self, investment_id: str):
        chunks = []
        for item in DEFAULT_WORKSPACE_CHUNKS:
            chunk = IndexedChunk(
                id=item["id"],
                document_name=item["document_name"],
                snippet=item["snippet"],
                page_number=item.get("page_number"),
                section_title=item.get("section_title"),
                metadata=item.get("metadata")
            )
            chunks.append(chunk)
        self._vector_store[investment_id] = chunks
        return len(chunks)

    def index_chunk(
        self,
        investment_id: str,
        document_name: str,
        snippet: str,
        page_number: Optional[int] = None,
        section_title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_id: Optional[str] = None
    ) -> IndexedChunk:
        cid = chunk_id or f"rag-chunk-{uuid.uuid4().hex[:8]}"
        chunk = IndexedChunk(
            id=cid,
            document_name=document_name,
            snippet=snippet,
            page_number=page_number,
            section_title=section_title,
            metadata=metadata
        )
        if investment_id not in self._vector_store:
            self._vector_store[investment_id] = []
        self._vector_store[investment_id].append(chunk)
        return chunk

    async def reindex_workspace(self, investment_id: str, db: Optional[AsyncSession] = None) -> int:
        """
        Re-indexes all workspace document chunks into the vector store.
        If DB session is provided, queries DocumentChunkModel records.
        Fallback to seed workspace documents if no DB chunks are found.
        """
        self._vector_store[investment_id] = []

        if db is not None:
            try:
                stmt = select(DocumentChunkModel, DocumentModel.filename).join(
                    DocumentModel, DocumentChunkModel.document_id == DocumentModel.id
                ).where(DocumentModel.investment_id == investment_id)
                res = await db.execute(stmt)
                rows = res.all()
                if rows:
                    for chunk_model, filename in rows:
                        self.index_chunk(
                            investment_id=investment_id,
                            document_name=filename,
                            snippet=chunk_model.content,
                            page_number=chunk_model.page_number,
                            section_title=chunk_model.section_title,
                            chunk_id=chunk_model.id
                        )
                    return len(self._vector_store[investment_id])
            except Exception:
                pass

        # Fallback to seed workspace chunks
        return self.seed_default_workspace(investment_id)

    def hybrid_search(
        self,
        investment_id: str,
        query: str,
        top_k: int = 5,
        min_hybrid_score: float = 0.0
    ) -> RAGQueryResponse:
        start_time = time.perf_counter()
        self._ensure_indexed(investment_id)

        query_embedding = generate_embedding(query)
        chunks = self._vector_store.get(investment_id, [])

        search_results: List[RAGSearchResult] = []

        for chunk in chunks:
            vector_score = cosine_similarity(query_embedding, chunk.embedding)
            keyword_score = compute_keyword_score(query, chunk.snippet)
            hybrid_score = round(0.7 * vector_score + 0.3 * keyword_score, 4)
            confidence = round(min(100.0, max(0.0, hybrid_score * 100)), 1)

            if hybrid_score >= min_hybrid_score:
                search_results.append(
                    RAGSearchResult(
                        id=chunk.id,
                        document_name=chunk.document_name,
                        page_number=chunk.page_number,
                        section_title=chunk.section_title,
                        snippet=chunk.snippet,
                        hybrid_score=hybrid_score,
                        vector_score=round(vector_score, 4),
                        keyword_score=round(keyword_score, 4),
                        confidence=confidence,
                        metadata=chunk.metadata
                    )
                )

        # Sort descending by hybrid_score
        search_results.sort(key=lambda r: r.hybrid_score, reverse=True)

        limited_results = search_results[:top_k]
        query_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return RAGQueryResponse(
            results=limited_results,
            total_results=len(search_results),
            query_time_ms=query_time_ms,
            top_k=top_k,
            min_hybrid_score=min_hybrid_score
        )


vector_rag_service = VectorRAGService()
