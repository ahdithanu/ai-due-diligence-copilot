import os
import tempfile
import pytest
from backend.services.document_parser import DocumentParserService

def test_parse_text_file():
    parser = DocumentParserService(chunk_size=100, overlap=20)
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("Executive Summary\nAcme Corp is a B2B SaaS leader with $12M ARR and 120% NRR.\n\nFinancial Performance\nGross margin is 82% across all products.")
        temp_path = f.name

    try:
        chunks = parser.parse_file(temp_path, "doc_test_1")
        assert len(chunks) > 0
        assert chunks[0].document_id == "doc_test_1"
        assert "Acme Corp" in chunks[0].content or "Executive Summary" in chunks[0].content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_extract_section_title():
    parser = DocumentParserService()
    title = parser._extract_section_title("Market Dynamics and Competitive Moat\nThe market is growing at 30% CAGR.")
    assert title == "Market Dynamics and Competitive Moat"
