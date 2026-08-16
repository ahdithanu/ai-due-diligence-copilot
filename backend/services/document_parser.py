import os
import re
import uuid
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
from backend.domain.schemas import DocumentChunk

class DocumentParserService:
    def __init__(self, chunk_size: int = 800, overlap: int = 150):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def parse_file(self, file_path: str, document_id: str) -> List[DocumentChunk]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self._parse_pdf(file_path, document_id)
        else:
            return self._parse_text(file_path, document_id)

    def _parse_pdf(self, file_path: str, document_id: str) -> List[DocumentChunk]:
        reader = PdfReader(file_path)
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            text = page.extract_text() or ""
            text = self._clean_text(text)
            
            if not text.strip():
                continue

            page_chunks = self._chunk_text(text)
            for chunk_text in page_chunks:
                section_title = self._extract_section_title(chunk_text)
                chunk = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    chunk_index=global_chunk_idx,
                    content=chunk_text,
                    page_number=page_num,
                    section_title=section_title,
                    char_count=len(chunk_text)
                )
                chunks.append(chunk)
                global_chunk_idx += 1

        return chunks

    def _parse_text(self, file_path: str, document_id: str) -> List[DocumentChunk]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        text = self._clean_text(text)
        chunks: List[DocumentChunk] = []
        raw_chunks = self._chunk_text(text)

        for idx, chunk_text in enumerate(raw_chunks):
            section_title = self._extract_section_title(chunk_text)
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                chunk_index=idx,
                content=chunk_text,
                page_number=1,
                section_title=section_title,
                char_count=len(chunk_text)
            )
            chunks.append(chunk)

        return chunks

    def _chunk_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            if end >= len(text):
                chunks.append(text[start:].strip())
                break
            
            # Try to break at a paragraph or sentence boundary
            break_point = text.rfind("\n\n", start, end)
            if break_point == -1 or break_point <= start:
                break_point = text.rfind(". ", start, end)
            if break_point == -1 or break_point <= start:
                break_point = end

            chunk_content = text[start:break_point].strip()
            if chunk_content:
                chunks.append(chunk_content)
            
            start = max(start + 1, break_point - self.overlap)

        return chunks

    def _clean_text(self, text: str) -> str:
        # Remove null bytes and excessive inline whitespace while preserving paragraph breaks
        text = text.replace("\x00", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    def _extract_section_title(self, text: str) -> str:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return "General Overview"
        first_line = lines[0]
        # If line looks like a header (short, capitalized, or numbered)
        if len(first_line) < 80:
            return first_line
        return first_line[:60] + "..."
