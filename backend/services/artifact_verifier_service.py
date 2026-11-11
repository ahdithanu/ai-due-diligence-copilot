import re
from typing import List, Tuple, Optional
from backend.domain.schemas import ArtifactComplianceReport

# Regex patterns for deterministic checks
ROUTING_ACCOUNT_PATTERN = re.compile(
    r"(?:routing|account|wire|acct|aba)[\s:#]+(\d{8,17})", re.IGNORECASE
)
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN (?:RSA )?PRIVATE KEY-----|[a-zA-Z0-9_-]{32,64}(?:secret|key|token)",
    re.IGNORECASE,
)

# Regulatory & SEC compliance promissory patterns
PROMISSORY_PATTERNS = [
    (re.compile(r"\bguarantee[d]?\b.*?\b(?:return|yield|profit|moic|irr)\b", re.IGNORECASE), "Guaranteed financial return claim"),
    (re.compile(r"\brisk[- ]?free\b", re.IGNORECASE), "Risk-free representation violates SEC Rule 156 / FINRA 2210"),
    (re.compile(r"\bcannot lose money\b", re.IGNORECASE), "Promissory downside statement"),
    (re.compile(r"\bassured\s+\d+x\b", re.IGNORECASE), "Assured multiple of capital representation"),
    (re.compile(r"\b100%\s+certain\b.*?\bexit\b", re.IGNORECASE), "Certainty representation on liquidity event"),
]


class ArtifactVerifierService:
    """
    Arca Chapter 7 & 12: Dual-Layer Edge Artifact Compliance Verifier.
    Every artifact produced from the sandbox runs:
    1. Deterministic checks for PII, raw wire details, SSNs, and cryptographic secrets.
    2. Regulatory compliance checks for promissory returns and ungrounded statements before publication.
    """

    def verify_artifact(
        self, artifact_name: str, content: str
    ) -> ArtifactComplianceReport:
        pii_findings: List[str] = []
        promissory_findings: List[str] = []
        ungrounded_findings: List[str] = []
        sanitized = content

        # 1. Deterministic PII / Wire checks
        for match in ROUTING_ACCOUNT_PATTERN.finditer(content):
            val = match.group(1)
            pii_findings.append(f"Raw banking/wire account number detected: {val[:3]}...{val[-4:]}")
            sanitized = sanitized.replace(val, "[REDACTED_BANK_ACCOUNT]")

        for match in SSN_PATTERN.finditer(content):
            val = match.group(0)
            pii_findings.append(f"Social Security Number / Tax ID detected: {val[:3]}-XX-XXXX")
            sanitized = sanitized.replace(val, "[REDACTED_SSN]")

        for match in PRIVATE_KEY_PATTERN.finditer(content):
            pii_findings.append("Cryptographic secret or private key pattern detected")

        # 2. Regulatory Promissory Claims checks
        for pat, desc in PROMISSORY_PATTERNS:
            if pat.search(content):
                promissory_findings.append(desc)

        # 3. Grounded Citation Checks
        # Memos with hard financial numbers ($XM ARR, $XM Valuation) should reference RAG chunks
        has_dollar_metrics = bool(re.search(r"\$\d+(?:\.\d+)?[MBK]", content))
        has_citations = "rag-chunk-" in content or "Source:" in content or "Citation:" in content
        if has_dollar_metrics and not has_citations and len(content) > 300:
            ungrounded_findings.append(
                "Document contains specific financial dollar metrics ($) without corresponding source chunk citations."
            )

        passed = (
            len(pii_findings) == 0
            and len(promissory_findings) == 0
            and len(ungrounded_findings) == 0
        )

        return ArtifactComplianceReport(
            artifact_name=artifact_name,
            passed=passed,
            pii_violations_count=len(pii_findings),
            pii_findings=pii_findings,
            promissory_claims_count=len(promissory_findings),
            promissory_findings=promissory_findings,
            ungrounded_claims_count=len(ungrounded_findings),
            ungrounded_findings=ungrounded_findings,
            sanitized_content=sanitized if not passed else content,
        )


artifact_verifier_service = ArtifactVerifierService()
