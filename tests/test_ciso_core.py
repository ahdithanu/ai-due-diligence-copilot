import pytest
from datetime import datetime, timezone
from backend.domain.schemas import (
    UserRole,
    TenantContext,
    DLPScanResult,
    AuditLogRecord,
    KMSKeyRecord,
    SOC2Report
)
from backend.services.tenant_service import (
    TenantService,
    TenantIsolationError,
    TenantValidationError,
    TenantNotFoundError
)
from backend.services.rbac_service import RBACService
from backend.services.dlp_service import DLPService


# =====================================================================
# Domain Schemas Tests
# =====================================================================

def test_user_role_enum():
    assert UserRole.SUPER_ADMIN == "SUPER_ADMIN"
    assert UserRole.IC_PARTNER == "IC_PARTNER"
    assert UserRole.DEAL_LEAD == "DEAL_LEAD"
    assert UserRole.ANALYST == "ANALYST"
    assert UserRole.EXTERNAL_LP_VIEWER == "EXTERNAL_LP_VIEWER"


def test_tenant_context_model():
    ctx = TenantContext(
        org_id="org_sequoia_apex",
        org_name="Apex Capital",
        user_id="user_123",
        user_email="partner@apexcap.com",
        role=UserRole.IC_PARTNER
    )
    assert ctx.org_id == "org_sequoia_apex"
    assert ctx.role == UserRole.IC_PARTNER
    dumped = ctx.model_dump()
    assert dumped["role"] == "IC_PARTNER"


def test_dlp_scan_result_model():
    res = DLPScanResult(
        original_text="Secret 123-45-6789",
        sanitized_text="Secret [REDACTED_SSN]",
        redacted_entities_count=1,
        detected_entity_types=["SSN"],
        is_clean=False
    )
    assert res.is_clean is False
    assert res.redacted_entities_count == 1
    assert "SSN" in res.detected_entity_types


def test_audit_log_record_model():
    rec = AuditLogRecord(
        actor_id="usr_admin",
        actor_role="SUPER_ADMIN",
        org_id="org_sec",
        action="UPDATE_SECURITY_POLICY",
        resource_type="KMS",
        resource_id="key_001",
        client_ip="10.0.0.1",
        prev_hash="0" * 64,
        entry_hash="abcdef123456"
    )
    assert rec.actor_role == "SUPER_ADMIN"
    assert rec.client_ip == "10.0.0.1"
    assert len(rec.id) > 0


def test_kms_key_record_model():
    key = KMSKeyRecord(
        key_id="kms_key_01",
        org_id="org_apex",
        status="ACTIVE",
        algorithm="AES-256-GCM"
    )
    assert key.status == "ACTIVE"
    assert key.algorithm == "AES-256-GCM"


def test_soc2_report_model():
    rep = SOC2Report(
        compliance_score_pct=100.0,
        status="COMPLIANT",
        controls_evaluated=6,
        controls_passed=6,
        details={"audit": "clean"}
    )
    assert rep.compliance_score_pct == 100.0
    assert rep.status == "COMPLIANT"


# =====================================================================
# TenantService & Multi-Tenant RLS Tests
# =====================================================================

@pytest.fixture
def tenant_svc():
    return TenantService()


def test_tenant_lifecycle(tenant_svc: TenantService):
    org = tenant_svc.create_organization(
        org_id="org_test_fund",
        org_name="Test Venture Fund",
        description="Seed Stage VC"
    )
    assert org["org_id"] == "org_test_fund"
    assert org["status"] == "ACTIVE"

    fetched = tenant_svc.get_organization("org_test_fund")
    assert fetched is not None
    assert fetched["org_name"] == "Test Venture Fund"

    updated = tenant_svc.update_organization("org_test_fund", org_name="Updated Fund")
    assert updated["org_name"] == "Updated Fund"

    deleted = tenant_svc.delete_organization("org_test_fund")
    assert deleted is True
    assert tenant_svc.get_organization("org_test_fund") is None


def test_tenant_user_assignment(tenant_svc: TenantService):
    tenant_svc.create_organization("org_deal_room", "Deal Room Capital")
    ctx = tenant_svc.assign_user_to_tenant(
        user_id="analyst_01",
        user_email="analyst@dealroom.com",
        org_id="org_deal_room",
        role=UserRole.ANALYST
    )
    assert ctx.user_id == "analyst_01"
    assert ctx.role == UserRole.ANALYST

    fetched_ctx = tenant_svc.get_user_context("analyst_01", "org_deal_room")
    assert fetched_ctx is not None
    assert fetched_ctx.org_name == "Deal Room Capital"


def test_tenant_isolation_rls_filtering(tenant_svc: TenantService):
    tenant_svc.create_organization("org_alpha", "Alpha Capital")
    tenant_svc.create_organization("org_beta", "Beta Ventures")

    ctx_alpha = tenant_svc.assign_user_to_tenant(
        user_id="user_a",
        user_email="a@alpha.com",
        org_id="org_alpha",
        role=UserRole.DEAL_LEAD
    )

    ctx_admin = tenant_svc.assign_user_to_tenant(
        user_id="admin_01",
        user_email="admin@platform.internal",
        org_id="org_alpha",
        role=UserRole.SUPER_ADMIN
    )

    records = [
        {"id": "deal_1", "company": "SaaS Alpha 1", "org_id": "org_alpha"},
        {"id": "deal_2", "company": "SaaS Alpha 2", "org_id": "org_alpha"},
        {"id": "deal_3", "company": "Health Beta 1", "org_id": "org_beta"},
    ]

    # Deal Lead at Alpha should only see Alpha deals
    alpha_records = tenant_svc.enforce_tenant_isolation(records, ctx_alpha)
    assert len(alpha_records) == 2
    assert all(r["org_id"] == "org_alpha" for r in alpha_records)

    # Super Admin can see all records
    admin_records = tenant_svc.enforce_tenant_isolation(records, ctx_admin)
    assert len(admin_records) == 3

    # Assert record access
    assert tenant_svc.validate_record_access(records[0], ctx_alpha) is True
    assert tenant_svc.validate_record_access(records[2], ctx_alpha) is False

    with pytest.raises(TenantIsolationError):
        tenant_svc.assert_record_access(records[2], ctx_alpha)


def test_cryptographic_audit_chain_integrity(tenant_svc: TenantService):
    tenant_svc.create_organization("org_audit_test", "Audit Capital")
    ctx = tenant_svc.assign_user_to_tenant(
        user_id="lead_01",
        user_email="lead@audit.com",
        org_id="org_audit_test",
        role=UserRole.DEAL_LEAD
    )

    tenant_svc.record_audit_log(
        actor_id=ctx.user_id,
        actor_role=ctx.role.value,
        org_id=ctx.org_id,
        action="EXPORT_INVESTMENT_MEMO",
        resource_type="MEMO",
        resource_id="memo_99"
    )

    assert tenant_svc.verify_audit_chain_integrity() is True
    logs = tenant_svc.get_audit_logs(ctx)
    assert len(logs) >= 2  # user assignment + export memo


def test_kms_and_soc2_report(tenant_svc: TenantService):
    tenant_svc.create_organization("org_soc2", "Compliance Ventures")
    ctx = tenant_svc.assign_user_to_tenant(
        user_id="ciso_01",
        user_email="ciso@soc2.com",
        org_id="org_soc2",
        role=UserRole.SUPER_ADMIN
    )

    keys = tenant_svc.get_tenant_kms_keys("org_soc2")
    assert len(keys) >= 1
    assert keys[0].status == "ACTIVE"

    report = tenant_svc.generate_soc2_report(ctx)
    assert report.compliance_score_pct == 100.0
    assert report.status == "COMPLIANT"
    assert report.controls_passed == report.controls_evaluated


# =====================================================================
# RBACService Tests
# =====================================================================

@pytest.fixture
def rbac_svc():
    return RBACService()


def test_rbac_permissions(rbac_svc: RBACService):
    # Super Admin can perform any action
    assert rbac_svc.check_permission(UserRole.SUPER_ADMIN, "anything") is True
    assert rbac_svc.check_permission(UserRole.SUPER_ADMIN, "delete_deal") is True

    # IC Partner can vote and approve
    assert rbac_svc.check_permission(UserRole.IC_PARTNER, "vote_ic") is True
    assert rbac_svc.check_permission(UserRole.IC_PARTNER, "approve_investment") is True
    assert rbac_svc.check_permission(UserRole.IC_PARTNER, "view_unmasked_memo") is True

    # Deal Lead can run diligence and edit deal, but cannot approve investment
    assert rbac_svc.check_permission(UserRole.DEAL_LEAD, "run_diligence") is True
    assert rbac_svc.check_permission(UserRole.DEAL_LEAD, "view_unmasked_memo") is True
    assert rbac_svc.check_permission(UserRole.DEAL_LEAD, "approve_investment") is False

    # Analyst cannot vote or view unmasked memo
    assert rbac_svc.check_permission(UserRole.ANALYST, "view_deal") is True
    assert rbac_svc.check_permission(UserRole.ANALYST, "run_diligence") is True
    assert rbac_svc.check_permission(UserRole.ANALYST, "view_unmasked_memo") is False
    assert rbac_svc.check_permission(UserRole.ANALYST, "vote_ic") is False

    # External LP Viewer is read-only
    assert rbac_svc.check_permission(UserRole.EXTERNAL_LP_VIEWER, "view_deal") is True
    assert rbac_svc.check_permission(UserRole.EXTERNAL_LP_VIEWER, "view_masked_memo") is True
    assert rbac_svc.check_permission(UserRole.EXTERNAL_LP_VIEWER, "create_deal") is False
    assert rbac_svc.check_permission(UserRole.EXTERNAL_LP_VIEWER, "run_diligence") is False


def test_rbac_document_masking(rbac_svc: RBACService):
    sample_text = (
        "Executive Summary: CEO Salary: $450,000 with $100,000 bonus. "
        "Founder equity: 42.5% across 2,500,000 common shares. "
        "ARR is $12M with 130% net retention. "
        "[CONFIDENTIAL: Target acquisition list]. "
        "CONFIDENTIAL: secret negotiation notes."
    )

    # Elevated roles see unmasked original content
    unmasked = rbac_svc.mask_document_content(sample_text, UserRole.IC_PARTNER)
    assert "$450,000" in unmasked
    assert "42.5%" in unmasked
    assert "[CONFIDENTIAL" in unmasked

    # Analyst sees masked content
    analyst_masked = rbac_svc.mask_document_content(sample_text, UserRole.ANALYST)
    assert "[REDACTED_EXECUTIVE_COMPENSATION]" in analyst_masked
    assert "$450,000" not in analyst_masked
    assert "[REDACTED_FOUNDER_EQUITY]" in analyst_masked
    assert "42.5%" not in analyst_masked
    assert "[REDACTED_CONFIDENTIAL]" in analyst_masked
    # Financial metrics should remain intact
    assert "ARR is $12M" in analyst_masked
    assert "130% net retention" in analyst_masked

    # External LP also sees masked content
    lp_masked = rbac_svc.mask_document_content(sample_text, UserRole.EXTERNAL_LP_VIEWER)
    assert "[REDACTED_EXECUTIVE_COMPENSATION]" in lp_masked
    assert "[REDACTED_FOUNDER_EQUITY]" in lp_masked


def test_rbac_sanitize_memo_for_role(rbac_svc: RBACService):
    raw_memo = {
        "memo_markdown": "# Memo\nCEO salary is $500,000. Founder equity: 35%. ARR: $8M.",
        "recommendation": "INVEST",
        "investment_thesis": "Strong growth with executive salary of $400k.",
        "skeptic_critique": "High valuation risk and customer concentration.",
        "ic_votes": {"Partner A": "YES", "Partner B": "YES"},
        "cap_table": [
            {"share_class": "Common", "investor_name": "Founder", "ownership_pct": 35.0, "shares_held": 3500000},
            {"share_class": "Series A", "investor_name": "Apex VC", "ownership_pct": 20.0, "shares_held": 2000000}
        ]
    }

    # IC Partner gets full unmasked memo
    partner_memo = rbac_svc.sanitize_memo_for_role(raw_memo, UserRole.IC_PARTNER)
    assert partner_memo["_is_masked"] is False
    assert "$500,000" in partner_memo["memo_markdown"]
    assert partner_memo["ic_votes"]["Partner A"] == "YES"

    # Analyst gets masked memo with cap table redacted for founders
    analyst_memo = rbac_svc.sanitize_memo_for_role(raw_memo, UserRole.ANALYST)
    assert analyst_memo["_is_masked"] is True
    assert "[REDACTED_EXECUTIVE_COMPENSATION]" in analyst_memo["memo_markdown"]
    assert analyst_memo["cap_table"][0]["shares_held"] == "[REDACTED_FOUNDER_EQUITY]"

    # External LP has internal IC votes and debate stripped/restricted
    lp_memo = rbac_svc.sanitize_memo_for_role(raw_memo, UserRole.EXTERNAL_LP_VIEWER)
    assert lp_memo["_is_masked"] is True
    assert lp_memo["skeptic_critique"] == "[RESTRICTED - INTERNAL IC USE ONLY]"
    assert lp_memo["ic_votes"] == "[RESTRICTED - INTERNAL IC USE ONLY]"


# =====================================================================
# DLPService Tests
# =====================================================================

@pytest.fixture
def dlp_svc():
    return DLPService()


def test_dlp_clean_text(dlp_svc: DLPService):
    clean = "Company revenue grew 85% year over year to reach $20,000,000 ARR in 2024."
    result = dlp_svc.scan_and_redact(clean)
    assert result.is_clean is True
    assert result.redacted_entities_count == 0
    assert len(result.detected_entity_types) == 0
    assert result.sanitized_text == clean
    assert dlp_svc.is_clean(clean) is True


def test_dlp_ssn_redaction(dlp_svc: DLPService):
    text = "Key employee tax ID is 987-65-4321."
    result = dlp_svc.scan_and_redact(text)
    assert result.is_clean is False
    assert "SSN" in result.detected_entity_types
    assert "[REDACTED_SSN]" in result.sanitized_text
    assert "987-65-4321" not in result.sanitized_text


def test_dlp_credit_card_redaction(dlp_svc: DLPService):
    text = "Corporate card on file: 4111-2222-3333-4444."
    result = dlp_svc.scan_and_redact(text)
    assert result.is_clean is False
    assert "CREDIT_CARD" in result.detected_entity_types
    assert "[REDACTED_CREDIT_CARD]" in result.sanitized_text
    assert "4111-2222-3333-4444" not in result.sanitized_text


def test_dlp_email_redaction(dlp_svc: DLPService):
    text = "Please reach out to alex.founder@stealthai.org for cap table inquiries."
    result = dlp_svc.scan_and_redact(text)
    assert result.is_clean is False
    assert "EMAIL" in result.detected_entity_types
    assert "[REDACTED_EMAIL]" in result.sanitized_text
    assert "alex.founder@stealthai.org" not in result.sanitized_text


def test_dlp_phone_redaction(dlp_svc: DLPService):
    text = "Direct line: (415) 555-0199 or mobile +1-415-555-0123."
    result = dlp_svc.scan_and_redact(text)
    assert result.is_clean is False
    assert "PHONE" in result.detected_entity_types
    assert "[REDACTED_PHONE]" in result.sanitized_text
    assert "555-0199" not in result.sanitized_text


def test_dlp_bank_account_redaction(dlp_svc: DLPService):
    text = "Wire routing number is 021000021 and account number is 12345678901."
    result = dlp_svc.scan_and_redact(text)
    assert result.is_clean is False
    assert "BANK_ACCOUNT" in result.detected_entity_types
    assert "[REDACTED_BANK_ACCOUNT]" in result.sanitized_text
    assert "021000021" not in result.sanitized_text


def test_dlp_comprehensive_scrubbing(dlp_svc: DLPService):
    complex_text = (
        "Founder Jane Doe (SSN: 123-45-6789, email: jane@seed.io, phone: 415-555-7890) "
        "provided bank wire details: routing 021000021, account 9876543210. "
        "Backup card: 5500-1234-5678-9012."
    )
    result = dlp_svc.scan_and_redact(complex_text)
    assert result.is_clean is False
    assert result.redacted_entities_count == 6
    assert set(result.detected_entity_types) == {"SSN", "EMAIL", "PHONE", "BANK_ACCOUNT", "CREDIT_CARD"}
    assert "[REDACTED_SSN]" in result.sanitized_text
    assert "[REDACTED_EMAIL]" in result.sanitized_text
    assert "[REDACTED_PHONE]" in result.sanitized_text
    assert "[REDACTED_BANK_ACCOUNT]" in result.sanitized_text
    assert "[REDACTED_CREDIT_CARD]" in result.sanitized_text


def test_dlp_dict_scrubbing(dlp_svc: DLPService):
    payload = {
        "deal": "Apollo",
        "contacts": [
            {"email": "cto@apollo.ai", "phone": "415-555-9988"},
            {"notes": "Clean notes without PII."}
        ],
        "banking": {
            "account": "123456789"
        }
    }
    scrubbed, count = dlp_svc.scrub_dict(payload)
    assert count == 3
    assert scrubbed["contacts"][0]["email"] == "[REDACTED_EMAIL]"
    assert scrubbed["contacts"][0]["phone"] == "[REDACTED_PHONE]"
    assert scrubbed["banking"]["account"] == "[REDACTED_BANK_ACCOUNT]"
    assert scrubbed["contacts"][1]["notes"] == "Clean notes without PII."
