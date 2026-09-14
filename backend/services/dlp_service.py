import re
import uuid
from typing import List, Dict, Any, Tuple, Optional
from backend.domain.schemas import DLPScanResult, DLPFinding, UserRole


class DLPService:
    r"""
    Enterprise Data Loss Prevention (DLP) & PII Scrubbing Service.
    
    Uses high-accuracy regex and token patterns to detect and redact:
    - SSNs / National IDs (\b\d{3}-\d{2}-\d{4}\b) -> [REDACTED_SSN]
    - Bank Account / Routing numbers (\b\d{9,12}\b) -> [REDACTED_BANK_ACCOUNT]
    - Credit Card numbers (\b(?:\d{4}[- ]?){3}\d{4}\b) -> [REDACTED_CREDIT_CARD]
    - Personal email addresses -> [REDACTED_EMAIL]
    - Phone numbers -> [REDACTED_PHONE]
    """

    # Exact patterns specified for enterprise CISO scanning
    PATTERNS: List[Tuple[str, re.Pattern, str]] = [
        (
            "CREDIT_CARD",
            re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b'),
            "[REDACTED_CREDIT_CARD]"
        ),
        (
            "SSN",
            re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "[REDACTED_SSN]"
        ),
        (
            "EMAIL",
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
            "[REDACTED_EMAIL]"
        ),
        (
            "PHONE",
            re.compile(
                r'(?:\+?1[-. ]?)?(?:\(\d{3}\)|\b\d{3})[-. ]\d{3}[-. ]\d{4}\b|'
                r'\b\+\d{1,3}[-. ]?\d{3,4}[-. ]?\d{3,4}[-. ]?\d{3,4}\b'
            ),
            "[REDACTED_PHONE]"
        ),
        (
            "BANK_ACCOUNT",
            re.compile(r'\b\d{9,12}\b'),
            "[REDACTED_BANK_ACCOUNT]"
        ),
        (
            "API_KEY",
            re.compile(r'\b(?:api_key_[0-9a-zA-Z]{20,}|Bearer\s+[A-Za-z0-9_\-\.]{20,})\b'),
            "[REDACTED_API_KEY]"
        ),
    ]

    def scan_and_redact(self, text: str) -> DLPScanResult:
        """
        Scans text for sensitive PII/financial entities and redacts them
        with standardized security tokens.
        """
        if not text:
            return DLPScanResult(
                original_text=text or "",
                sanitized_text=text or "",
                redacted_entities_count=0,
                detected_entity_types=[],
                is_clean=True,
                status="CLEAN"
            )

        sanitized = text
        detected_types: List[str] = []
        findings: List[DLPFinding] = []
        total_redacted = 0

        for entity_type, pattern, replacement in self.PATTERNS:
            for match in pattern.finditer(sanitized):
                matched_val = match.group(0)
                findings.append(DLPFinding(
                    entity_type=entity_type,
                    original_text=matched_val,
                    redacted_token=replacement,
                    start_offset=match.start(),
                    end_offset=match.end(),
                    confidence_score=0.98
                ))

            matches = pattern.findall(sanitized)
            if matches:
                count = len(matches)
                total_redacted += count
                if entity_type not in detected_types:
                    detected_types.append(entity_type)
                sanitized = pattern.sub(replacement, sanitized)

        is_clean = (total_redacted == 0)
        return DLPScanResult(
            original_text=text,
            sanitized_text=sanitized,
            redacted_text=sanitized,
            redacted_entities_count=total_redacted,
            detected_entity_types=detected_types,
            is_clean=is_clean,
            findings=findings,
            status="CLEAN" if is_clean else "REDACTED"
        )

    def scan(self, text: str) -> List[Dict[str, Any]]:
        """Detailed entity findings for DLP scan."""
        findings: List[Dict[str, Any]] = []
        if not text:
            return findings

        for entity_type, pattern, _ in self.PATTERNS:
            for m in pattern.finditer(text):
                findings.append({
                    "entity_type": entity_type,
                    "start": m.start(),
                    "end": m.end(),
                    "matched_text": m.group()
                })
        findings.sort(key=lambda x: x["start"])
        return findings

    def is_clean(self, text: str) -> bool:
        """Fast boolean check for clean text without PII."""
        if not text:
            return True
        for _, pattern, _ in self.PATTERNS:
            if pattern.search(text):
                return False
        return True

    def scrub_dict(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Recursively scrubs strings in dicts/lists."""
        total_redactions = 0

        def _scrub(item: Any) -> Any:
            nonlocal total_redactions
            if isinstance(item, str):
                result = self.scan_and_redact(item)
                total_redactions += result.redacted_entities_count
                return result.sanitized_text
            elif isinstance(item, dict):
                return {k: _scrub(v) for k, v in item.items()}
            elif isinstance(item, list):
                return [_scrub(v) for v in item]
            return item

        sanitized_data = _scrub(data)
        return sanitized_data, total_redactions


# Aliases & Singletons
DLPScannerService = DLPService
dlp_service = DLPService()

def get_dlp_service() -> DLPService:
    return dlp_service


# ==========================================
# RBAC & Content Masking Helper Functions
# ==========================================

ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "SUPER_ADMIN": ["kms_manage", "kms_revoke", "audit_export", "diligence_run", "view_unmasked", "approve_ic", "view_deal"],
    "IC_PARTNER": ["audit_export", "diligence_run", "view_unmasked", "approve_ic", "view_deal"],
    "DEAL_LEAD": ["diligence_run", "view_unmasked", "edit_memo", "view_deal"],
    "ANALYST": ["diligence_run", "view_deal", "submit_review"],
    "EXTERNAL_LP_VIEWER": ["view_teaser", "view_lp_portal"],
}


def normalize_role(role: Any) -> str:
    """Normalizes role representations (e.g. 'LP Viewer' -> 'EXTERNAL_LP_VIEWER')."""
    if isinstance(role, UserRole):
        return role.value
    r = str(role).strip().upper().replace(" ", "_")
    if r in ("LP_VIEWER", "EXTERNAL_LP_VIEWER"):
        return "EXTERNAL_LP_VIEWER"
    if r in ("ANALYST",):
        return "ANALYST"
    if r in ("DEAL_LEAD", "LEAD"):
        return "DEAL_LEAD"
    if r in ("IC_PARTNER", "PARTNER"):
        return "IC_PARTNER"
    if r in ("SUPER_ADMIN", "ADMIN"):
        return "SUPER_ADMIN"
    return r


def check_permission(role: Any, action: str) -> bool:
    """Evaluates whether a role has permission to perform a security action."""
    norm_role = normalize_role(role)
    perms = ROLE_PERMISSIONS.get(norm_role, [])
    return action in perms


def mask_document_content(content: str, role: Any) -> str:
    """
    Applies role-based document content masking:
    - IC_PARTNER, DEAL_LEAD, SUPER_ADMIN: Unmasked view.
    - ANALYST: Redacts PII, SSN, bank accounts, credit cards via DLP scanner.
    - EXTERNAL_LP_VIEWER: Masks sensitive internal deliberation and financials,
      restricting to LP teaser view.
    """
    norm_role = normalize_role(role)
    
    if norm_role in ("SUPER_ADMIN", "IC_PARTNER", "DEAL_LEAD"):
        return content
        
    if norm_role == "ANALYST":
        scan_res = dlp_service.scan_and_redact(content)
        return scan_res.sanitized_text
        
    if norm_role == "EXTERNAL_LP_VIEWER":
        scan_res = dlp_service.scan_and_redact(content)
        sanitized = scan_res.sanitized_text
        masked_lines = []
        for line in sanitized.splitlines():
            if any(term in line.lower() for term in ["valuation", "cap table", "burn rate", "ebitda", "payout", "partner vote"]):
                masked_lines.append("[RESTRICTED FOR LP - CONFIDENTIAL INVESTMENT COMMITTEE PROPERTY]")
            else:
                masked_lines.append(line)
        return "\n".join(masked_lines)
        
    return dlp_service.scan_and_redact(content).sanitized_text


def enforce_tenant_isolation(user_org_id: str, resource_org_id: str):
    """Raises PermissionError if a cross-organization access attempt occurs."""
    if user_org_id != resource_org_id:
        raise PermissionError(
            f"Tenant Isolation Violation: Caller org '{user_org_id}' cannot access resource owned by org '{resource_org_id}'."
        )
