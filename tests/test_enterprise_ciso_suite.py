import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.services.crypto_service import EnvelopeEncryptionService, crypto_service
from backend.services.audit_service import ImmutableAuditService, audit_service
from backend.services.dlp_service import (
    DLPScannerService, dlp_service, mask_document_content,
    check_permission, enforce_tenant_isolation
)
from backend.domain.schemas import UserRole


# ==========================================
# 1. Tenant Isolation & Cross-Org Access Tests
# ==========================================

def test_tenant_isolation_encryption_and_cross_org_rejection():
    """Verify data encrypted for Tenant A cannot be decrypted by Tenant B."""
    service = EnvelopeEncryptionService()
    org_a = "org-apex-saas"
    org_b = "org-horizon-buyout"

    secret_payload = b"Confidential M&A Term Sheet with Valuation Multiples"
    package = service.encrypt_data(secret_payload, org_id=org_a)

    # Decrypting under Tenant A succeeds
    decrypted_a = service.decrypt_data(package, org_id=org_a)
    assert decrypted_a == secret_payload

    # Cross-tenant decryption attempt by Tenant B MUST be rejected
    with pytest.raises(PermissionError) as exc_info:
        service.decrypt_data(package, org_id=org_b)
    assert "Tenant isolation violation" in str(exc_info.value)


def test_enforce_tenant_isolation_boundary():
    """Verify tenant isolation boundary checker helper."""
    # Matching tenant passes
    enforce_tenant_isolation("tenant-100", "tenant-100")

    # Mismatched tenant raises PermissionError
    with pytest.raises(PermissionError) as exc_info:
        enforce_tenant_isolation("tenant-100", "tenant-200")
    assert "Tenant Isolation Violation" in str(exc_info.value)


def test_audit_logs_tenant_filtering():
    """Verify audit logs can be filtered strictly by organization."""
    svc = ImmutableAuditService()
    svc.log_event("user-1", "DEAL_LEAD", "org-alpha", "READ_DEAL", "DEAL", "deal-1")
    svc.log_event("user-2", "ANALYST", "org-beta", "READ_DEAL", "DEAL", "deal-2")

    alpha_logs = svc.list_logs(org_id="org-alpha")
    beta_logs = svc.list_logs(org_id="org-beta")

    assert all(r.org_id == "org-alpha" for r in alpha_logs)
    assert any(r.action == "READ_DEAL" for r in alpha_logs)
    assert all(r.org_id == "org-beta" for r in beta_logs)
    assert not any(r.org_id == "org-beta" for r in alpha_logs)


# ==========================================
# 2. RBAC Permissions & Content Masking Tests
# ==========================================

def test_rbac_permission_matrix():
    """Verify granular permissions for all enterprise roles."""
    # SUPER_ADMIN has full permissions
    assert check_permission(UserRole.SUPER_ADMIN, "kms_revoke") is True
    assert check_permission(UserRole.SUPER_ADMIN, "audit_export") is True
    assert check_permission(UserRole.SUPER_ADMIN, "view_unmasked") is True

    # IC_PARTNER can view unmasked and approve IC, but cannot revoke KMS keys
    assert check_permission(UserRole.IC_PARTNER, "view_unmasked") is True
    assert check_permission(UserRole.IC_PARTNER, "approve_ic") is True
    assert check_permission(UserRole.IC_PARTNER, "kms_revoke") is False

    # DEAL_LEAD can view unmasked and edit memos
    assert check_permission(UserRole.DEAL_LEAD, "view_unmasked") is True
    assert check_permission(UserRole.DEAL_LEAD, "edit_memo") is True
    assert check_permission(UserRole.DEAL_LEAD, "audit_export") is False

    # ANALYST cannot view unmasked sensitive PII and cannot revoke KMS keys
    assert check_permission(UserRole.ANALYST, "diligence_run") is True
    assert check_permission(UserRole.ANALYST, "view_unmasked") is False
    assert check_permission(UserRole.ANALYST, "kms_revoke") is False

    # EXTERNAL_LP_VIEWER is strictly restricted to teaser view
    assert check_permission(UserRole.EXTERNAL_LP_VIEWER, "view_teaser") is True
    assert check_permission(UserRole.EXTERNAL_LP_VIEWER, "view_unmasked") is False
    assert check_permission(UserRole.EXTERNAL_LP_VIEWER, "diligence_run") is False


def test_document_content_masking_for_analyst_and_lp():
    """Verify document content masking differences between Partner, Analyst, and LP Viewer."""
    raw_document = (
        "Project Orion: ARR is $15M.\n"
        "Founder SSN: 987-65-4321 and Personal Wire Account: 1234567890.\n"
        "Investment Committee Valuation is $65M with 3.5x MoIC target.\n"
        "Partner Vote: Unanimous Approval."
    )

    # 1. Partner sees full unmasked content
    partner_view = mask_document_content(raw_document, UserRole.IC_PARTNER)
    assert partner_view == raw_document

    # 2. Analyst sees operational data, but PII (SSN, Bank Account) is masked
    analyst_view = mask_document_content(raw_document, UserRole.ANALYST)
    assert "987-65-4321" not in analyst_view
    assert "[REDACTED_SSN]" in analyst_view
    assert "1234567890" not in analyst_view
    assert "[REDACTED_BANK_ACCOUNT]" in analyst_view
    assert "$15M" in analyst_view  # Operational ARR metric still accessible

    # 3. LP Viewer sees teaser level: confidential IC Valuation & votes are masked
    lp_view = mask_document_content(raw_document, UserRole.EXTERNAL_LP_VIEWER)
    assert "987-65-4321" not in lp_view
    assert "[RESTRICTED FOR LP" in lp_view
    assert "Valuation is $65M" not in lp_view


# ==========================================
# 3. DLP Scanner Tests (SSN, Bank, Credit Cards)
# ==========================================

def test_dlp_scanner_detects_and_masks_pii_and_financials():
    """Verify DLP scanner redacts SSNs, credit cards, bank accounts, emails, and API keys."""
    scanner = DLPScannerService()
    test_text = (
        "Client Record: SSN 123-45-6789. "
        "Credit Card charged: 4111-2222-3333-4444. "
        "Routing / Bank Account: 9876543210. "
        "Direct contact: lead-partner@apexvc.com. "
        "Leaked credential: api_key_sampledemotestingkey123456."
    )

    result = scanner.scan_and_redact(test_text)

    assert result.is_clean is False
    assert result.status == "REDACTED"
    assert result.redacted_entities_count >= 5

    # Check that original sensitive strings are absent in sanitized_text
    assert "123-45-6789" not in result.sanitized_text
    assert "4111-2222-3333-4444" not in result.sanitized_text
    assert "9876543210" not in result.sanitized_text
    assert "lead-partner@apexvc.com" not in result.sanitized_text
    assert "sk_live_" not in result.sanitized_text

    # Check that redaction tokens are inserted
    assert "[REDACTED_SSN]" in result.sanitized_text
    assert "[REDACTED_CREDIT_CARD]" in result.sanitized_text
    assert "[REDACTED_BANK_ACCOUNT]" in result.sanitized_text
    assert "[REDACTED_EMAIL]" in result.sanitized_text
    assert "[REDACTED_API_KEY]" in result.sanitized_text

    # Check detected entity types
    assert "SSN" in result.detected_entity_types
    assert "CREDIT_CARD" in result.detected_entity_types
    assert "BANK_ACCOUNT" in result.detected_entity_types


def test_dlp_scanner_clean_text_passthrough():
    """Verify clean text passes through without alteration."""
    scanner = DLPScannerService()
    clean_text = "The target company has grown 45% YoY with an NRR of 125% and positive unit economics."
    result = scanner.scan_and_redact(clean_text)

    assert result.is_clean is True
    assert result.status == "CLEAN"
    assert result.redacted_entities_count == 0
    assert result.sanitized_text == clean_text
    assert len(result.detected_entity_types) == 0


# ==========================================
# 4. KMS Envelope Encryption & Revocation Shredding
# ==========================================

def test_kms_envelope_encryption_and_tamper_proofing():
    """Verify AES-256-GCM envelope encryption, DEK wrapping, and tampering detection."""
    kms = EnvelopeEncryptionService()
    org_id = "org-test-firm"
    payload = b"Confidential Proprietary Valuation Model"

    package = kms.encrypt_data(payload, org_id=org_id)

    # Validate package structure
    assert package["algorithm"] == "AES-256-GCM"
    assert package["org_id"] == org_id
    assert "ciphertext" in package
    assert "wrapped_dek" in package
    assert "iv" in package
    assert "tag" in package
    assert "dek_iv" in package
    assert "dek_tag" in package

    # Decrypt and verify equality
    decrypted = kms.decrypt_data(package, org_id=org_id)
    assert decrypted == payload

    # Tampering test: modify ciphertext
    tampered_package = dict(package)
    # Alter ciphertext by replacing last character of base64 string
    tampered_package["tag"] = "QUFBQUFBQUFBQUFBQUFBQQ=="
    with pytest.raises(ValueError):
        kms.decrypt_data(tampered_package, org_id=org_id)


def test_kms_cryptographic_shredding_via_key_revocation():
    """
    Verify cryptographic shredding: revoking customer master key
    renders previously encrypted payloads permanently unreadable.
    """
    kms = EnvelopeEncryptionService()
    org_id = "org-shred-target"
    secret = b"Top Secret Acquisition Bid Strategy"

    package = kms.encrypt_data(secret, org_id=org_id)
    assert kms.decrypt_data(package, org_id=org_id) == secret

    # Revoke customer key (Simulate Cryptographic Shredding)
    revoked_record = kms.revoke_customer_key(org_id=org_id)
    assert revoked_record.status == "REVOKED"

    # Attempting to decrypt the existing ciphertext package now MUST fail
    with pytest.raises(ValueError) as exc_info:
        kms.decrypt_data(package, org_id=org_id)
    assert "Cryptographically shredded" in str(exc_info.value)

    # Attempting to encrypt new data under revoked key MUST fail
    with pytest.raises(ValueError):
        kms.encrypt_data(b"New data", org_id=org_id)


# ==========================================
# 5. Immutable Audit Log Hash-Chain Integrity Tests
# ==========================================

def test_immutable_audit_hash_chain_validity_and_tamper_detection():
    """Verify SHA-256 hash chaining and immediate detection of any log modification."""
    audit = ImmutableAuditService()
    initial_verification = audit.verify_chain_integrity()
    assert initial_verification["chain_valid"] is True
    initial_count = initial_verification["total_records"]

    # Add new audit records
    rec1 = audit.log_event(
        actor_id="user-lead",
        actor_role="DEAL_LEAD",
        org_id="org-apex",
        action="MEMO_GENERATED",
        resource_type="MEMO",
        resource_id="memo-456",
        client_ip="192.168.1.50"
    )
    rec2 = audit.log_event(
        actor_id="partner-alice",
        actor_role="IC_PARTNER",
        org_id="org-apex",
        action="IC_APPROVED",
        resource_type="MEMO",
        resource_id="memo-456",
        client_ip="192.168.1.51"
    )

    # Verify chain linking
    assert rec2.prev_hash == rec1.entry_hash
    chain_check = audit.verify_chain_integrity()
    assert chain_check["chain_valid"] is True
    assert chain_check["total_records"] == initial_count + 2
    assert chain_check["latest_hash"] == rec2.entry_hash

    # Simulate adversary tampering with a historical record in the SIEM store
    audit._logs[1].action = "MALICIOUS_UNAUTHORIZED_CHANGE"
    tampered_check = audit.verify_chain_integrity()
    assert tampered_check["chain_valid"] is False
    assert tampered_check["tampered_index"] == 1
    assert "invalid at index 1" in tampered_check["error"]


# ==========================================
# 6. Security REST API Integration Tests
# ==========================================

@pytest.mark.asyncio
async def test_security_rest_api_endpoints():
    """Test full suite of /api/v1/security REST endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/v1/security/audit-logs
        logs_resp = await client.get("/api/v1/security/audit-logs")
        assert logs_resp.status_code == 200
        logs_data = logs_resp.json()
        assert isinstance(logs_data, list)
        assert len(logs_data) > 0
        assert "entry_hash" in logs_data[0]
        assert "actor_id" in logs_data[0]

        # 2. GET /api/v1/security/verify-integrity
        integrity_resp = await client.get("/api/v1/security/verify-integrity")
        assert integrity_resp.status_code == 200
        integrity_data = integrity_resp.json()
        assert integrity_data["chain_valid"] is True
        assert integrity_data["total_records"] > 0
        assert integrity_data["genesis_hash"] is not None

        # 3. GET /api/v1/security/kms-status
        kms_resp = await client.get("/api/v1/security/kms-status?org_id=org-api-test")
        assert kms_resp.status_code == 200
        kms_data = kms_resp.json()
        assert kms_data["org_id"] == "org-api-test"
        assert kms_data["status"] == "ACTIVE"
        assert kms_data["algorithm"] == "AES-256-GCM"
        assert "key_id" in kms_data

        # 4. POST /api/v1/security/dlp-scan
        dlp_resp = await client.post("/api/v1/security/dlp-scan", json={
            "text": "Deal contact SSN: 123-45-6789 and Card: 4111-2222-3333-4444."
        })
        assert dlp_resp.status_code == 200
        dlp_data = dlp_resp.json()
        assert dlp_data["is_clean"] is False
        assert "[REDACTED_SSN]" in dlp_data["sanitized_text"]
        assert "[REDACTED_CREDIT_CARD]" in dlp_data["sanitized_text"]
        assert dlp_data["redacted_entities_count"] == 2

        # 5. POST /api/v1/security/kms-revoke (Cryptographic shredding)
        revoke_resp = await client.post("/api/v1/security/kms-revoke", json={
            "org_id": "org-api-test"
        })
        assert revoke_resp.status_code == 200
        revoke_data = revoke_resp.json()
        assert revoke_data["status"] == "REVOKED"

        # Verify KMS status reflects revoked
        kms_check_resp = await client.get("/api/v1/security/kms-status?org_id=org-api-test")
        assert kms_check_resp.status_code == 200
        assert kms_check_resp.json()["status"] == "REVOKED"

        # 6. GET /api/v1/security/soc2-report
        soc2_resp = await client.get("/api/v1/security/soc2-report")
        assert soc2_resp.status_code == 200
        soc2_data = soc2_resp.json()
        assert soc2_data["compliance_score_pct"] >= 80.0
        assert soc2_data["audit_readiness_status"] in ["Audit Ready", "In Progress"]
        assert soc2_data["controls_evaluated"] == 5
        assert any(c["id"] == "CC6.1" for c in soc2_data["controls"])
        assert any(c["id"] == "CC6.6" for c in soc2_data["controls"])
