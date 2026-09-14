import copy
import re
from typing import Dict, Any, List, Optional, Set
from backend.domain.schemas import UserRole


class RBACService:
    """
    Enterprise Role-Based Access Control (RBAC) & Document Masking Service.
    
    Roles:
    - SUPER_ADMIN: Full system & organization privileges, bypasses masking.
    - IC_PARTNER: Investment Committee partner. Full diligence access, unmasked data, voting, approval.
    - DEAL_LEAD: Leads deals and diligence. Unmasked access to diligence data, cannot approve investment.
    - ANALYST: Evaluates deals. Sees masked executive compensation, masked founder equity, and confidential data.
    - EXTERNAL_LP_VIEWER: Read-only external limited partner viewer. Sees masked memos, strictly restricted
      from internal IC debates, voting, executive compensation, and raw cap tables.
    """

    # Role-Action Matrix
    PERMISSIONS_MAP: Dict[UserRole, Set[str]] = {
        UserRole.SUPER_ADMIN: {"*"},
        UserRole.IC_PARTNER: {
            "view_deal", "create_deal", "edit_deal", "delete_deal",
            "run_diligence", "rerun_diligence",
            "view_memo", "view_unmasked_memo", "view_masked_memo",
            "vote_ic", "approve_investment", "reject_investment",
            "export_pdf", "view_audit_logs", "view_cap_table", "view_unmasked_comp",
            "view_metrics", "access_data_room"
        },
        UserRole.DEAL_LEAD: {
            "view_deal", "create_deal", "edit_deal",
            "run_diligence", "rerun_diligence",
            "view_memo", "view_unmasked_memo", "view_masked_memo",
            "export_pdf", "view_cap_table", "view_unmasked_comp",
            "view_metrics", "access_data_room"
        },
        UserRole.ANALYST: {
            "view_deal", "create_deal", "edit_deal",
            "run_diligence", "view_memo", "view_masked_memo",
            "view_metrics", "access_data_room", "export_pdf"
        },
        UserRole.EXTERNAL_LP_VIEWER: {
            "view_deal", "view_memo", "view_masked_memo"
        }
    }

    # Regex patterns for Executive Compensation Masking
    _COMPENSATION_PATTERNS = [
        # Match label followed by amount: "salary: $450,000", "total comp: $500k", "bonus: $100,000"
        (
            re.compile(
                r'(?i)(\b(?:salary|base\s+salary|base\s+pay|annual\s+salary|executive\s+comp(?:ensation)?|total\s+comp(?:ensation)?|bonus|severance(?:\s+package)?)\s*(?:is|of|:|=|\bat\b)?\s*)'
                r'(\$?\d+(?:,\d{3})*(?:\.\d+)?(?:\s+(?:k|m|million|usd|dollars))?(?:/(?:year|yr|mo|month|annum))?)'
            ),
            r'\1[REDACTED_EXECUTIVE_COMPENSATION]'
        ),
        # Match amount followed by comp label: "$500,000 base salary", "$100,000 bonus"
        (
            re.compile(
                r'(?i)(\$?\d+(?:,\d{3})*(?:\.\d+)?(?:\s+(?:k|m|million|usd))?)\s+'
                r'((?:base\s+salary|base\s+pay|executive\s+salary|annual\s+salary|executive\s+bonus|severance(?:\s+package)?|executive\s+comp(?:ensation)?|bonus|salary)\b)'
            ),
            r'[REDACTED_EXECUTIVE_COMPENSATION] \2'
        ),
        # Match "compensation of $1,200,000"
        (
            re.compile(
                r'(?i)(\b(?:compensation|comp|package)\s+of\s+)'
                r'(\$?\d+(?:,\d{3})*(?:\.\d+)?(?:\s+(?:k|m|million|usd))?)'
            ),
            r'\1[REDACTED_EXECUTIVE_COMPENSATION]'
        )
    ]

    # Regex patterns for Founder Equity & Cap Table Ownership Masking
    _EQUITY_PATTERNS = [
        # "founder equity: 42.5%", "founder ownership: 51%", "co-founder equity: 30%"
        (
            re.compile(
                r'(?i)(\b(?:founder\s+equity|founder\s+ownership|founding\s+team\s+equity|co-founder\s+equity|founder\s+stake)\s*(?:is|of|:|=|\bat\b)?\s*)'
                r'(\d+(?:\.\d+)?%)'
            ),
            r'\1[REDACTED_FOUNDER_EQUITY]'
        ),
        # "founder holds 42%", "CEO owns 35%", "founding team holds 60%"
        (
            re.compile(
                r'(?i)(\b(?:founder|co-founder|founding\s+team|ceo|cto)\s+(?:holds|owns|retains|has)\s*)'
                r'(\d+(?:\.\d+)?%)'
            ),
            r'\1[REDACTED_FOUNDER_EQUITY]'
        ),
        # "founder holds 2,500,000 shares", "CEO owns 1,000,000 common shares"
        (
            re.compile(
                r'(?i)(\b(?:founder|co-founder|ceo|cto)\s+(?:holds|owns|retains)\s*)'
                r'([\d,]+\s*(?:common\s+|preferred\s+)?shares\b)'
            ),
            r'\1[REDACTED_FOUNDER_EQUITY]'
        ),
        # "across 2,500,000 common shares"
        (
            re.compile(
                r'(?i)(\b(?:across|holds|owns|retains|has|with)\s+)'
                r'([\d,]+\s*(?:common\s+|preferred\s+)?shares\b)'
            ),
            r'\1[REDACTED_FOUNDER_EQUITY]'
        ),
        # "equity stake: 35%"
        (
            re.compile(
                r'(?i)(\b(?:equity\s+stake|equity\s+ownership|ownership\s+stake)\s*(?:is|of|:|=|\bat\b)?\s*)'
                r'(\d+(?:\.\d+)?%)'
            ),
            r'\1[REDACTED_FOUNDER_EQUITY]'
        )
    ]

    # Regex patterns for Confidential Data Masking
    _CONFIDENTIAL_PATTERNS = [
        re.compile(r'\[CONFIDENTIAL(?::\s*[^\]]+)?\]', re.IGNORECASE),
        re.compile(r'(?i)\bCONFIDENTIAL:\s*[^\n,;]+'),
        re.compile(r'(?i)\bRESTRICTED:\s*[^\n,;]+'),
        re.compile(r'(?i)\bPROPRIETARY:\s*[^\n,;]+'),
        re.compile(r'(?i)\b(?:api[_-]?key|secret[_-]?key|password|access[_-]?token)\s*[:=]\s*[\'"]?([a-zA-Z0-9_\-\.]{8,})[\'"]?')
    ]

    def check_permission(self, role: UserRole, action: str) -> bool:
        """
        Validates whether a given UserRole possesses authorization for the requested action.
        """
        if role == UserRole.SUPER_ADMIN:
            return True

        normalized_action = action.strip().lower().replace("-", "_")
        role_permissions = self.PERMISSIONS_MAP.get(role, set())

        if "*" in role_permissions:
            return True

        return normalized_action in role_permissions

    def mask_document_content(self, content: str, role: UserRole) -> str:
        """
        Masks executive compensation, founder equity, and confidential data for
        ANALYST or EXTERNAL_LP_VIEWER roles.
        
        SUPER_ADMIN, IC_PARTNER, and DEAL_LEAD view unmasked content.
        """
        if not content:
            return content

        # Elevated roles view original unmasked document content
        if role in (UserRole.SUPER_ADMIN, UserRole.IC_PARTNER, UserRole.DEAL_LEAD):
            return content

        masked_text = content

        # 1. Mask Executive Compensation
        for pattern, repl in self._COMPENSATION_PATTERNS:
            masked_text = pattern.sub(repl, masked_text)

        # 2. Mask Founder Equity & Cap Table Ownership
        for pattern, repl in self._EQUITY_PATTERNS:
            masked_text = pattern.sub(repl, masked_text)

        # 3. Mask Confidential Data
        for pattern in self._CONFIDENTIAL_PATTERNS:
            masked_text = pattern.sub("[REDACTED_CONFIDENTIAL]", masked_text)

        return masked_text

    def sanitize_memo_for_role(self, memo: Dict[str, Any], role: UserRole) -> Dict[str, Any]:
        """
        Sanitizes investment memo payload based on the caller's role.
        - Unmasked for SUPER_ADMIN, IC_PARTNER, DEAL_LEAD.
        - Masked compensation/equity/confidential for ANALYST and EXTERNAL_LP_VIEWER.
        - EXTERNAL_LP_VIEWER additionally has internal IC votes, partner debate,
          and skeptic critique omitted or marked restricted.
        """
        sanitized = copy.deepcopy(memo)

        # Mark metadata
        sanitized["_access_role"] = role.value

        if role in (UserRole.SUPER_ADMIN, UserRole.IC_PARTNER, UserRole.DEAL_LEAD):
            sanitized["_is_masked"] = False
            return sanitized

        sanitized["_is_masked"] = True

        # Sanitize text fields
        text_fields = [
            "memo_markdown", "investment_thesis", "bull_case",
            "bear_case", "base_case", "recommendation_notes", "notes"
        ]
        for field in text_fields:
            if field in sanitized and isinstance(sanitized[field], str):
                sanitized[field] = self.mask_document_content(sanitized[field], role)

        # Sanitize cap table if present
        if "cap_table" in sanitized and isinstance(sanitized["cap_table"], list):
            sanitized_cap_table = []
            for entry in sanitized["cap_table"]:
                e_copy = dict(entry)
                # Redact founder/executive equity numbers
                if any(kw in str(e_copy.get("share_class", "")).lower() or
                       kw in str(e_copy.get("investor_name", "")).lower()
                       for kw in ["founder", "common", "management", "option pool"]):
                    e_copy["shares_held"] = "[REDACTED_FOUNDER_EQUITY]"
                    e_copy["ownership_pct"] = "[REDACTED_FOUNDER_EQUITY]"
                sanitized_cap_table.append(e_copy)
            sanitized["cap_table"] = sanitized_cap_table

        # Additional restrictions for EXTERNAL_LP_VIEWER
        if role == UserRole.EXTERNAL_LP_VIEWER:
            # Mask or restrict internal skeptic debate
            if "skeptic_critique" in sanitized:
                sanitized["skeptic_critique"] = "[RESTRICTED - INTERNAL IC USE ONLY]"

            # Strip internal IC votes & partner debate
            restricted_keys = [
                "ic_votes", "internal_notes", "partner_feedback",
                "ic_audio_script", "failure_details", "checkpoint_history"
            ]
            for r_key in restricted_keys:
                if r_key in sanitized:
                    sanitized[r_key] = "[RESTRICTED - INTERNAL IC USE ONLY]"

        return sanitized


# Global Service Singleton
_rbac_service_instance: Optional[RBACService] = None

def get_rbac_service() -> RBACService:
    """Returns the global RBACService singleton."""
    global _rbac_service_instance
    if _rbac_service_instance is None:
        _rbac_service_instance = RBACService()
    return _rbac_service_instance
