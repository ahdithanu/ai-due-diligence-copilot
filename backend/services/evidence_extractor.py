import re
import uuid
from typing import List, Dict, Any
from backend.domain.schemas import DocumentChunk, EvidenceRecord, ClaimType

class EvidenceExtractorService:
    def __init__(self):
        # Regex patterns for deterministic evidence extraction
        self.financial_pattern = re.compile(
            r"(\b(?:ARR|MRR|Revenue|Gross Margin|Operating Margin|EBITDA|Net Income|CAC|LTV|NRR|Burn Rate|Runway|Cash|Valuation)\b[^\n.]{0,100}?"
            r"(?:\$?\d+(?:\.\d+)?\s*(?:M|B|K|million|billion|k|%)?))",
            re.IGNORECASE
        )
        self.metric_value_pattern = re.compile(
            r"(\b[A-Za-z0-9_\s]{2,30}\b)\s*(?:=|:|\bis\b|\bwas\b|\bhits\b|\breached\b)\s*(\$?\d+(?:\.\d+)?\s*(?:M|B|K|million|billion|k|%)?)",
            re.IGNORECASE
        )

    def extract_evidence(self, chunks: List[DocumentChunk]) -> List[EvidenceRecord]:
        records: List[EvidenceRecord] = []

        for chunk in chunks:
            # 1. Financial/Metric deterministic extraction
            fin_matches = self.financial_pattern.findall(chunk.content)
            for match in fin_matches:
                cleaned_content = match.strip()
                if len(cleaned_content) > 10:
                    rec = EvidenceRecord(
                        id=str(uuid.uuid4()),
                        document_id=chunk.document_id,
                        chunk_id=chunk.id,
                        content=cleaned_content,
                        page_number=chunk.page_number,
                        section_title=chunk.section_title,
                        confidence=0.95,
                        claim_type=ClaimType.FACT,
                        metadata={"extraction_method": "pattern_match", "category": "financial_metric"}
                    )
                    records.append(rec)

            # 2. General sentence extraction for factual claims
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", chunk.content) if len(s.strip()) > 20]
            for sentence in sentences:
                # Avoid duplicate if sentence was already matched by pattern
                if any(r.content in sentence or sentence in r.content for r in records if r.chunk_id == chunk.id):
                    continue

                claim_type = self._classify_claim_type(sentence)
                rec = EvidenceRecord(
                    id=str(uuid.uuid4()),
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    content=sentence,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    confidence=0.85,
                    claim_type=claim_type,
                    metadata={"extraction_method": "rule_based", "category": "general_claim"}
                )
                records.append(rec)

        return records

    def _classify_claim_type(self, text: str) -> ClaimType:
        lower_text = text.lower()
        if any(w in lower_text for w in ["calculate", "computed", "sum", "total", "margin =", "growth ="]):
            return ClaimType.CALCULATION
        elif any(w in lower_text for w in ["expect", "project", "forecast", "assume", "estimate", "believe"]):
            return ClaimType.ASSUMPTION
        elif any(w in lower_text for w in ["suggests", "indicates", "implies", "appears to"]):
            return ClaimType.INFERENCE
        elif any(w in lower_text for w in ["unclear", "unknown", "missing", "tbd", "todo"]):
            return ClaimType.UNRESOLVED_QUESTION
        else:
            return ClaimType.FACT
