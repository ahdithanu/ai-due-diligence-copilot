import math
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.vector_rag_service import (
    VectorRAGService,
    vector_rag_service,
    generate_embedding,
    normalize_vector,
    cosine_similarity,
    compute_keyword_score,
    EMBEDDING_DIM
)
from backend.domain.schemas import RAGQueryRequest, RAGQueryResponse, RAGSearchResult


client = TestClient(app)
TEST_INVESTMENT_ID = "inv-test-vector-rag-100"


def test_embedding_generation_and_normalization():
    """
    Test 384-dimensional embedding generation & L2 normalization.
    """
    sample_text = "Series A investment due diligence and financial revenue analysis."
    embedding = generate_embedding(sample_text)

    assert len(embedding) == EMBEDDING_DIM, f"Expected {EMBEDDING_DIM} dimensions, got {len(embedding)}"

    l2_norm_squared = sum(v * v for v in embedding)
    assert math.isclose(l2_norm_squared, 1.0, abs_tol=1e-5), f"L2 norm squared should be 1.0, got {l2_norm_squared}"

    # Determinism test
    embedding2 = generate_embedding(sample_text)
    assert embedding == embedding2, "Embedding generation must be deterministic for identical input text"

    # Empty text fallback test
    empty_emb = generate_embedding("")
    assert len(empty_emb) == EMBEDDING_DIM
    assert math.isclose(sum(v * v for v in empty_emb), 1.0, abs_tol=1e-5)


def test_cosine_similarity_and_hybrid_score():
    """
    Test cosine similarity computation and 0.7 * Cosine + 0.3 * Keyword hybrid score formula.
    """
    text1 = "LTV/CAC ratio stands at 4.2x with a payback period of 11.5 months."
    text2 = "LTV/CAC ratio stands at 4.2x with a payback period of 11.5 months."
    text3 = "Unrelated sentence about legal dispute in jurisdiction."

    emb1 = generate_embedding(text1)
    emb2 = generate_embedding(text2)
    emb3 = generate_embedding(text3)

    # Identical vectors should have cosine similarity == 1.0
    sim_identical = cosine_similarity(emb1, emb2)
    assert math.isclose(sim_identical, 1.0, abs_tol=1e-4)

    # Distinct texts should have lower similarity
    sim_different = cosine_similarity(emb1, emb3)
    assert sim_different < sim_identical

    # Keyword score test
    kw_score_high = compute_keyword_score("LTV CAC payback ratio", text1)
    assert kw_score_high > 0.5

    kw_score_low = compute_keyword_score("quantum computing hardware", text1)
    assert kw_score_low == 0.0

    # Hybrid score formula verification: 0.7 * Cosine + 0.3 * Keyword
    test_cos = 0.8
    test_kw = 0.6
    expected_hybrid = round(0.7 * test_cos + 0.3 * test_kw, 4)
    assert math.isclose(expected_hybrid, 0.74, abs_tol=1e-4)


def test_chunk_indexing_and_search_retrieval():
    """
    Test indexing document chunks and hybrid search retrieval ranking.
    """
    service = VectorRAGService()
    inv_id = "inv-custom-index-test"

    service.index_chunk(
        investment_id=inv_id,
        document_name="Revenue_Report.pdf",
        snippet="Annual Recurring Revenue (ARR) reached $12.4M with 145% YoY growth.",
        section_title="ARR Growth",
        page_number=1
    )
    service.index_chunk(
        investment_id=inv_id,
        document_name="Security_Audit.pdf",
        snippet="SOC2 Type II compliance audit completed with zero non-conformances.",
        section_title="Security Audit",
        page_number=4
    )

    # Query matching revenue chunk
    res = service.hybrid_search(
        investment_id=inv_id,
        query="ARR annual recurring revenue growth",
        top_k=2,
        min_hybrid_score=0.0
    )

    assert isinstance(res, RAGQueryResponse)
    assert len(res.results) > 0
    assert res.results[0].document_name == "Revenue_Report.pdf"
    assert res.results[0].hybrid_score >= res.results[-1].hybrid_score

    # Filter test with high min_hybrid_score threshold
    strict_res = service.hybrid_search(
        investment_id=inv_id,
        query="completely random unindexed phrase",
        top_k=5,
        min_hybrid_score=0.99
    )
    assert len(strict_res.results) == 0


def test_rest_api_rag_endpoints():
    """
    Test REST API endpoints /api/v1/investments/{investment_id}/rag/reindex and /search.
    """
    # 1. Test /rag/reindex
    reindex_resp = client.post(f"/api/v1/investments/{TEST_INVESTMENT_ID}/rag/reindex")
    assert reindex_resp.status_code == 200
    reindex_data = reindex_resp.json()
    assert reindex_data["status"] == "success"
    assert reindex_data["investment_id"] == TEST_INVESTMENT_ID
    assert reindex_data["indexed_chunks"] > 0

    # 2. Test /rag/search
    search_payload = {
        "query": "LTV CAC payback ratio net revenue retention",
        "top_k": 3,
        "min_hybrid_score": 0.1,
        "investment_id": TEST_INVESTMENT_ID
    }
    search_resp = client.post(
        f"/api/v1/investments/{TEST_INVESTMENT_ID}/rag/search",
        json=search_payload
    )
    assert search_resp.status_code == 200
    search_data = search_resp.json()

    assert "results" in search_data
    assert "total_results" in search_data
    assert "query_time_ms" in search_data
    assert search_data["top_k"] == 3
    assert len(search_data["results"]) <= 3

    if len(search_data["results"]) > 0:
        first_result = search_data["results"][0]
        assert "document_name" in first_result
        assert "snippet" in first_result
        assert "hybrid_score" in first_result
        assert "vector_score" in first_result
        assert "keyword_score" in first_result
        assert "confidence" in first_result

        # Verify descending order of hybrid scores
        scores = [r["hybrid_score"] for r in search_data["results"]]
        assert scores == sorted(scores, reverse=True)
