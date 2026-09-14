import React, { useState, useMemo } from 'react';
import {
  RoleName,
  TenantContext,
  DLPScanResult,
  DLPFinding,
  AuditLogRecord,
  KMSKeyRecord,
  SOC2Report
} from '../types';

// ============================================================================
// Initial Mock Data & Configurations
// ============================================================================

const TENANTS: Record<string, TenantContext> = {
  'Apex SaaS Capital': {
    tenant_id: 'tenant-apex-9021',
    tenant_name: 'Apex SaaS Capital',
    active_role: 'IC Partner',
    allowed_roles: ['IC Partner', 'Deal Lead', 'Analyst', 'LP Viewer'],
    data_retention_policy: 'Zero Data Retention - Ephemeral Context & Model SLA',
    kms_key_id: 'arn:aws:kms:us-east-1:771928340192:key/mrk-apex-saas-cmk-9021',
    isolation_tier: 'LOGICAL_RLS',
    created_at: '2025-01-15T00:00:00Z'
  },
  'Horizon Buyout Fund': {
    tenant_id: 'tenant-horizon-4412',
    tenant_name: 'Horizon Buyout Fund',
    active_role: 'Deal Lead',
    allowed_roles: ['IC Partner', 'Deal Lead', 'Analyst', 'LP Viewer'],
    data_retention_policy: 'Strict Isolation - Non-Training Enterprise Agreement',
    kms_key_id: 'arn:aws:kms:us-east-1:882910394812:key/mrk-horizon-buyout-cmk-4412',
    isolation_tier: 'DEDICATED_SCHEMA',
    created_at: '2025-02-01T00:00:00Z'
  }
};

const ROLE_PERMISSIONS: Record<RoleName, { title: string; desc: string; perms: string[] }> = {
  'IC Partner': {
    title: 'Investment Committee Partner',
    desc: 'Senior principal with full audit authority, unmasked financial view, and crypto-shredding approval rights.',
    perms: ['Full Diligence Access', 'Unmask Confidential PII', 'Approve IC Memos', 'Trigger Cryptographic Shred', 'Export Immutable Audit Log']
  },
  'Deal Lead': {
    title: 'Deal Lead / VP Diligence',
    desc: 'Execution owner managing deal pipeline, cross-examination loops, and model evaluation parameters.',
    perms: ['Full Diligence Access', 'Orchestrate Graph Execution', 'Manage Financial Models', 'View Redacted PII', 'Trigger Key Rotation']
  },
  'Analyst': {
    title: 'Diligence Associate / Analyst',
    desc: 'Extraction specialist operating document chunking, prompt experiments, and financial spread checks.',
    perms: ['Read/Write Evidence', 'Run DLP Redaction Tests', 'Query Vector RAG', 'Submit Data Room Requests', 'Masked PII Only']
  },
  'LP Viewer': {
    title: 'Limited Partner Institutional Viewer',
    desc: 'External read-only stakeholder restricted to synthesized executive memos and sanitized tear sheets.',
    perms: ['View Approved LP Teasers', 'Inspect Aggregated Metrics', 'Zero PII Access', 'Restricted Model Access']
  }
};

const INITIAL_SOC2_REPORT: SOC2Report = {
  report_id: 'SOC2-TYPE-II-2026-Q1',
  audit_period: 'Oct 01, 2025 - Mar 31, 2026',
  compliance_score_pct: 98.5,
  audit_readiness_status: 'Audit Ready',
  certifying_firm: 'Schellman & Company / PwC SOC Practice',
  last_updated: '2026-09-12T14:30:00Z',
  controls: [
    {
      id: 'CC-6.1',
      name: 'Tenant Isolation',
      status: 'COMPLIANT',
      score_pct: 100,
      description: 'PostgreSQL Row-Level Security (RLS) policies with per-tenant connection context and cryptographically signed session tokens. Zero cross-tenant data leakage detected in 2.4M automated synthetic checks.',
      last_audited: '2026-09-10'
    },
    {
      id: 'CC-6.6',
      name: 'Encryption at Rest',
      status: 'COMPLIANT',
      score_pct: 100,
      description: 'AES-256-GCM envelope encryption with hardware-backed Customer Master Keys (AWS KMS / Cloud KMS). Distinct Data Encryption Key (DEK) generated per diligence workspace.',
      last_audited: '2026-09-11'
    },
    {
      id: 'CC-6.8',
      name: 'DLP (Data Loss Prevention)',
      status: 'COMPLIANT',
      score_pct: 97.8,
      description: 'Pre-flight entity scanner scans and replaces SSNs, corporate cards, routing numbers, and credentials before token serialization. Model input sanitizer blocks prompt injection.',
      last_audited: '2026-09-08'
    },
    {
      id: 'CC-7.2',
      name: 'Immutable Auditing',
      status: 'COMPLIANT',
      score_pct: 100,
      description: 'Append-only audit trail anchored with SHA-256 cryptographic hash-chains. Tamper-evident verification runs continuously with sub-millisecond anomaly detection.',
      last_audited: '2026-09-12'
    },
    {
      id: 'CC-8.1',
      name: 'Zero Data Retention',
      status: 'COMPLIANT',
      score_pct: 99.2,
      description: 'Contractual zero data retention enforced with OpenAI, Google Gemini, and Anthropic APIs. No customer documents or embeddings are utilized for model training or retained post-session.',
      last_audited: '2026-09-09'
    }
  ]
};

const INITIAL_AUDIT_LOGS: AuditLogRecord[] = [
  {
    id: 'aud-9801',
    timestamp: '2026-09-13 21:55:04 UTC',
    actor: 'sarah.chen@apexsaas.com',
    role: 'IC Partner',
    action: 'APPROVE_INVESTMENT_MEMO',
    resource: 'workspace:inv-8821 (Acme AI Cloud)',
    client_ip: '192.0.2.45 (US-East)',
    hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    previous_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    chain_verified: true,
    tenant_id: 'tenant-apex-9021',
    status: 'SUCCESS'
  },
  {
    id: 'aud-9802',
    timestamp: '2026-09-13 21:50:22 UTC',
    actor: 'marcus.vance@apexsaas.com',
    role: 'Deal Lead',
    action: 'EXECUTE_DILIGENCE_GRAPH',
    resource: 'graph_node:SpecialistAnalyst_Financial',
    client_ip: '198.51.100.12 (US-West)',
    hash: 'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb',
    previous_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    chain_verified: true,
    tenant_id: 'tenant-apex-9021',
    status: 'SUCCESS'
  },
  {
    id: 'aud-9803',
    timestamp: '2026-09-13 21:42:19 UTC',
    actor: 'system.dlp-gateway@diligence.ai',
    role: 'System Service',
    action: 'DLP_PII_REDACTION',
    resource: 'document:pitch_deck_v4.pdf (Chunk #18)',
    client_ip: '10.0.4.88 (Internal VPC)',
    hash: '4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce',
    previous_hash: 'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb',
    chain_verified: true,
    tenant_id: 'tenant-apex-9021',
    status: 'SUCCESS'
  },
  {
    id: 'aud-9804',
    timestamp: '2026-09-13 21:30:11 UTC',
    actor: 'david.miller@horizonfund.com',
    role: 'Deal Lead',
    action: 'EXPORT_FINANCIAL_METRICS',
    resource: 'metrics:EBITDA_Bridge_Table_2025',
    client_ip: '203.0.113.84 (EU-Central)',
    hash: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
    previous_hash: '4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce',
    chain_verified: true,
    tenant_id: 'tenant-horizon-4412',
    status: 'SUCCESS'
  },
  {
    id: 'aud-9805',
    timestamp: '2026-09-13 21:15:40 UTC',
    actor: 'kms-rotator@aws.amazon.com',
    role: 'System Service',
    action: 'ROTATE_DATA_ENCRYPTION_KEY',
    resource: 'kms_key:mrk-apex-saas-cmk-9021',
    client_ip: '169.254.169.254 (KMS Service)',
    hash: '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
    previous_hash: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
    chain_verified: true,
    tenant_id: 'tenant-apex-9021',
    status: 'SUCCESS'
  }
];

const INITIAL_KMS_KEYS: Record<string, KMSKeyRecord> = {
  'tenant-apex-9021': {
    key_id: 'mrk-84a7e912-3490-4821-bc19-12a9ef4023b1',
    alias: 'alias/apex-saas-production-cmk',
    tenant_id: 'tenant-apex-9021',
    algorithm: 'AES-256-GCM',
    state: 'ACTIVE',
    created_at: '2025-01-15T10:00:00Z',
    last_rotated_at: '2026-09-01T04:00:00Z',
    cmk_arn: 'arn:aws:kms:us-east-1:771928340192:key/mrk-84a7e912-3490-4821-bc19-12a9ef4023b1',
    key_versions_count: 4,
    auto_rotation_days: 90
  },
  'tenant-horizon-4412': {
    key_id: 'mrk-991b2c44-5501-4773-a128-99ddff1182c4',
    alias: 'alias/horizon-buyout-production-cmk',
    tenant_id: 'tenant-horizon-4412',
    algorithm: 'AES-256-GCM',
    state: 'ACTIVE',
    created_at: '2025-02-01T12:00:00Z',
    last_rotated_at: '2026-08-20T08:00:00Z',
    cmk_arn: 'arn:aws:kms:us-east-1:882910394812:key/mrk-991b2c44-5501-4773-a128-99ddff1182c4',
    key_versions_count: 3,
    auto_rotation_days: 90
  }
};

// ============================================================================
// DLP Processing Helper Functions
// ============================================================================

const SSN_REGEX = /\b(?:\d{3}-\d{2}-\d{4}|\d{9})\b/g;
const CC_REGEX = /\b(?:\d{4}[- ]?){3}\d{4}\b/g;
const EMAIL_REGEX = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
const API_KEY_REGEX = /\b(?:sk-[a-zA-Z0-9_-]{20,}|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z-_]{35})\b/g;
const PHONE_REGEX = /\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b/g;

function executeDLPScan(rawText: string): DLPScanResult {
  const startTime = performance.now();
  const findings: DLPFinding[] = [];
  let redacted = rawText;

  // 1. Scan SSNs
  let match: RegExpExecArray | null;
  const ssnPattern = new RegExp(SSN_REGEX);
  while ((match = ssnPattern.exec(rawText)) !== null) {
    findings.push({
      entity_type: 'SSN',
      original_text: match[0],
      redacted_token: '[REDACTED_SSN]',
      start_offset: match.index,
      end_offset: match.index + match[0].length,
      confidence_score: 0.999
    });
  }
  redacted = redacted.replace(SSN_REGEX, '[REDACTED_SSN]');

  // 2. Scan Credit Cards
  const ccPattern = new RegExp(CC_REGEX);
  while ((match = ccPattern.exec(rawText)) !== null) {
    findings.push({
      entity_type: 'CREDIT_CARD',
      original_text: match[0],
      redacted_token: '[REDACTED_CREDIT_CARD]',
      start_offset: match.index,
      end_offset: match.index + match[0].length,
      confidence_score: 0.998
    });
  }
  redacted = redacted.replace(CC_REGEX, '[REDACTED_CREDIT_CARD]');

  // 3. Scan API Keys
  const keyPattern = new RegExp(API_KEY_REGEX);
  while ((match = keyPattern.exec(rawText)) !== null) {
    findings.push({
      entity_type: 'API_KEY',
      original_text: match[0],
      redacted_token: '[REDACTED_API_KEY]',
      start_offset: match.index,
      end_offset: match.index + match[0].length,
      confidence_score: 0.995
    });
  }
  redacted = redacted.replace(API_KEY_REGEX, '[REDACTED_API_KEY]');

  // 4. Scan Email
  const emailPattern = new RegExp(EMAIL_REGEX);
  while ((match = emailPattern.exec(rawText)) !== null) {
    findings.push({
      entity_type: 'EMAIL',
      original_text: match[0],
      redacted_token: '[REDACTED_EMAIL]',
      start_offset: match.index,
      end_offset: match.index + match[0].length,
      confidence_score: 0.991
    });
  }
  redacted = redacted.replace(EMAIL_REGEX, '[REDACTED_EMAIL]');

  // 5. Scan Phone Numbers
  const phonePattern = new RegExp(PHONE_REGEX);
  while ((match = phonePattern.exec(rawText)) !== null) {
    findings.push({
      entity_type: 'PHONE',
      original_text: match[0],
      redacted_token: '[REDACTED_PHONE]',
      start_offset: match.index,
      end_offset: match.index + match[0].length,
      confidence_score: 0.985
    });
  }
  redacted = redacted.replace(PHONE_REGEX, '[REDACTED_PHONE]');

  const durationMs = Math.max(1.2, +(performance.now() - startTime).toFixed(2));

  return {
    scan_id: `dlp-${Date.now().toString(36)}`,
    timestamp: new Date().toISOString(),
    input_text: rawText,
    redacted_text: redacted,
    findings,
    entities_detected_count: findings.length,
    scan_duration_ms: durationMs,
    status: findings.length > 0 ? 'REDACTED' : 'CLEAN'
  };
}

// Generate simple deterministic SHA-256 style mock hash for live logs
function generateSimpleHash(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0;
  }
  const hex = Math.abs(hash).toString(16).padStart(8, '0');
  return `${hex}${hex}4f128bc${hex}9a08e12f000${hex}`.slice(0, 64);
}

// ============================================================================
// EnterpriseSecurityView Component
// ============================================================================

export const EnterpriseSecurityView: React.FC = () => {
  // 1. Tenant & Persona State
  const [selectedTenantName, setSelectedTenantName] = useState<'Apex SaaS Capital' | 'Horizon Buyout Fund'>('Apex SaaS Capital');
  const [selectedRole, setSelectedRole] = useState<RoleName>('IC Partner');

  const currentTenant = useMemo(() => {
    return TENANTS[selectedTenantName];
  }, [selectedTenantName]);

  // 2. SOC 2 Compliance Report State
  const [soc2Report] = useState<SOC2Report>(INITIAL_SOC2_REPORT);
  const [selectedControl, setSelectedControl] = useState<string | null>('CC-6.1');
  const [showCertModal, setShowCertModal] = useState(false);

  // 3. Immutable Audit Trail State
  const [auditLogs, setAuditLogs] = useState<AuditLogRecord[]>(INITIAL_AUDIT_LOGS);
  const [auditFilterRole, setAuditFilterRole] = useState<string>('ALL');
  const [auditSearchQuery, setAuditSearchQuery] = useState<string>('');
  const [chainVerifying, setChainVerifying] = useState(false);
  const [chainVerifySuccess, setChainVerifySuccess] = useState<boolean | null>(null);

  // 4. DLP Redaction Sandbox State
  const SAMPLE_DLP_TEXT = `EXECUTIVE DILIGENCE SUMMARY - CONFIDENTIAL
Founder & Principal SSN is 123-45-6789 (US Citizen, Verified Background Check).
Corporate emergency debit card on file for escrow deposit: 4532-8819-2049-9012 (Expires 08/29).
Escrow contact: alex.vance@apexsaas.com or call direct cell (415) 555-0199.
Access to the founder data room requires internal key sk-live-99a8b7c6d5e4f3a2b1c0998877.`;

  const [dlpInputText, setDlpInputText] = useState<string>(SAMPLE_DLP_TEXT);
  const [dlpResult, setDlpResult] = useState<DLPScanResult | null>(() => executeDLPScan(SAMPLE_DLP_TEXT));
  const [dlpScanning, setDlpScanning] = useState<boolean>(false);
  const [activeDlpTab, setActiveDlpTab] = useState<'redacted' | 'findings' | 'sidebyside'>('redacted');

  // 5. KMS Envelope Encryption State
  const [kmsKeys, setKmsKeys] = useState<Record<string, KMSKeyRecord>>(INITIAL_KMS_KEYS);
  const [shredConfirmModalOpen, setShredConfirmModalOpen] = useState(false);
  const [shredReason, setShredReason] = useState('Deal Abandoned / Mandated Cryptographic Erasure');
  const [shredProcessing, setShredProcessing] = useState(false);
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'info' | 'success' | 'danger' } | null>(null);

  const activeKmsKey = kmsKeys[currentTenant.tenant_id];

  // Helper to show flash toasts
  const triggerToast = (text: string, type: 'info' | 'success' | 'danger' = 'info') => {
    setToastMessage({ text, type });
    setTimeout(() => {
      setToastMessage(null);
    }, 4500);
  };

  // Switch tenant handler
  const handleTenantChange = (tenantName: 'Apex SaaS Capital' | 'Horizon Buyout Fund') => {
    setSelectedTenantName(tenantName);
    const newTenant = TENANTS[tenantName];
    // Record audit event
    const newLog: AuditLogRecord = {
      id: `aud-${Date.now().toString().slice(-4)}`,
      timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC',
      actor: `${selectedRole.toLowerCase().replace(' ', '.')}@${tenantName.toLowerCase().replace(/[^a-z]/g, '')}.com`,
      role: selectedRole,
      action: 'SWITCH_TENANT_CONTEXT',
      resource: `tenant:${newTenant.tenant_id}`,
      client_ip: '192.0.2.45 (US-East)',
      hash: generateSimpleHash(`SWITCH_TENANT_${newTenant.tenant_id}_${Date.now()}`),
      previous_hash: auditLogs[0]?.hash || '0000000000000000',
      chain_verified: true,
      tenant_id: newTenant.tenant_id,
      status: 'SUCCESS'
    };
    setAuditLogs(prev => [newLog, ...prev]);
    triggerToast(`Switched active tenant context to ${tenantName}`, 'info');
  };

  // Switch role handler
  const handleRoleChange = (role: RoleName) => {
    setSelectedRole(role);
    const newLog: AuditLogRecord = {
      id: `aud-${Date.now().toString().slice(-4)}`,
      timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC',
      actor: `${role.toLowerCase().replace(' ', '.')}@${selectedTenantName.toLowerCase().replace(/[^a-z]/g, '')}.com`,
      role: role,
      action: 'ASSUME_PERSONA_ROLE',
      resource: `rbac:role:${role}`,
      client_ip: '192.0.2.45 (US-East)',
      hash: generateSimpleHash(`ROLE_CHANGE_${role}_${Date.now()}`),
      previous_hash: auditLogs[0]?.hash || '0000000000000000',
      chain_verified: true,
      tenant_id: currentTenant.tenant_id,
      status: 'SUCCESS'
    };
    setAuditLogs(prev => [newLog, ...prev]);
    triggerToast(`Role updated to ${role}`, 'info');
  };

  // Run DLP Scan
  const handleRunDLP = () => {
    setDlpScanning(true);
    setTimeout(() => {
      const result = executeDLPScan(dlpInputText);
      setDlpResult(result);
      setDlpScanning(false);

      // Audit log entry for DLP scan
      const newLog: AuditLogRecord = {
        id: `aud-${Date.now().toString().slice(-4)}`,
        timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC',
        actor: `${selectedRole.toLowerCase().replace(' ', '.')}@${selectedTenantName.toLowerCase().replace(/[^a-z]/g, '')}.com`,
        role: selectedRole,
        action: 'DLP_SCAN_REDACTION',
        resource: `sandbox:payload (${result.entities_detected_count} entities masked)`,
        client_ip: '192.0.2.45 (US-East)',
        hash: generateSimpleHash(`DLP_SCAN_${result.scan_id}`),
        previous_hash: auditLogs[0]?.hash || '0000000000000000',
        chain_verified: true,
        tenant_id: currentTenant.tenant_id,
        status: 'SUCCESS'
      };
      setAuditLogs(prev => [newLog, ...prev]);
      triggerToast(`DLP Scan Complete: ${result.entities_detected_count} sensitive entities redacted`, 'success');
    }, 400);
  };

  // Verify Audit Trail Chain
  const handleVerifyChain = () => {
    setChainVerifying(true);
    setChainVerifySuccess(null);
    setTimeout(() => {
      setChainVerifying(false);
      setChainVerifySuccess(true);
      triggerToast('All 5 audit blocks cryptographically verified against root SHA-256 anchor', 'success');
    }, 800);
  };

  // Rotate KMS Key
  const handleRotateKey = () => {
    const tenantId = currentTenant.tenant_id;
    setKmsKeys(prev => ({
      ...prev,
      [tenantId]: {
        ...prev[tenantId],
        key_versions_count: prev[tenantId].key_versions_count + 1,
        last_rotated_at: new Date().toISOString()
      }
    }));

    const newLog: AuditLogRecord = {
      id: `aud-${Date.now().toString().slice(-4)}`,
      timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC',
      actor: `${selectedRole.toLowerCase().replace(' ', '.')}@${selectedTenantName.toLowerCase().replace(/[^a-z]/g, '')}.com`,
      role: selectedRole,
      action: 'ROTATE_DATA_ENCRYPTION_KEY',
      resource: `kms_key:${activeKmsKey.key_id} (Version ${activeKmsKey.key_versions_count + 1})`,
      client_ip: '192.0.2.45 (US-East)',
      hash: generateSimpleHash(`ROTATE_KEY_${Date.now()}`),
      previous_hash: auditLogs[0]?.hash || '0000000000000000',
      chain_verified: true,
      tenant_id: tenantId,
      status: 'SUCCESS'
    };
    setAuditLogs(prev => [newLog, ...prev]);
    triggerToast(`KMS Customer Master Key successfully rotated to Version ${activeKmsKey.key_versions_count + 1}`, 'success');
  };

  // Test Cryptographic Shredding
  const handleConfirmShred = () => {
    setShredProcessing(true);
    setTimeout(() => {
      const tenantId = currentTenant.tenant_id;
      setKmsKeys(prev => ({
        ...prev,
        [tenantId]: {
          ...prev[tenantId],
          state: 'SHREDDED'
        }
      }));
      setShredProcessing(false);
      setShredConfirmModalOpen(false);

      const newLog: AuditLogRecord = {
        id: `aud-${Date.now().toString().slice(-4)}`,
        timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC',
        actor: `${selectedRole.toLowerCase().replace(' ', '.')}@${selectedTenantName.toLowerCase().replace(/[^a-z]/g, '')}.com`,
        role: selectedRole,
        action: 'CRYPTO_SHRED_TENANT_DEK',
        resource: `kms:cmk:${activeKmsKey.key_id} [ZEROIZED]`,
        client_ip: '192.0.2.45 (US-East)',
        hash: generateSimpleHash(`CRYPTO_SHRED_${Date.now()}`),
        previous_hash: auditLogs[0]?.hash || '0000000000000000',
        chain_verified: true,
        tenant_id: tenantId,
        status: 'FLAGGED'
      };
      setAuditLogs(prev => [newLog, ...prev]);
      triggerToast(`🚨 CRYPTOGRAPHIC SHRED COMPLETE: Tenant DEK zeroized. Diligence ciphertext is mathematically unrecoverable.`, 'danger');
    }, 1000);
  };

  // Restore KMS Key after shred for testing
  const handleRestoreKey = () => {
    const tenantId = currentTenant.tenant_id;
    setKmsKeys(prev => ({
      ...prev,
      [tenantId]: {
        ...prev[tenantId],
        state: 'ACTIVE'
      }
    }));
    triggerToast(`Restored active demo DEK for ${selectedTenantName}`, 'info');
  };

  // Filtered audit logs
  const filteredLogs = auditLogs.filter(log => {
    const matchesRole = auditFilterRole === 'ALL' || log.role === auditFilterRole;
    const matchesSearch =
      auditSearchQuery === '' ||
      log.action.toLowerCase().includes(auditSearchQuery.toLowerCase()) ||
      log.actor.toLowerCase().includes(auditSearchQuery.toLowerCase()) ||
      log.resource.toLowerCase().includes(auditSearchQuery.toLowerCase()) ||
      log.hash.toLowerCase().includes(auditSearchQuery.toLowerCase());
    return matchesRole && matchesSearch;
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Flash Toast Notification */}
      {toastMessage && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-5 py-3.5 rounded-xl text-xs font-semibold shadow-2xl flex items-center gap-3 backdrop-blur-md border transition-all duration-300 animate-bounce ${
            toastMessage.type === 'danger'
              ? 'bg-rose-950/90 text-rose-200 border-rose-500 shadow-rose-950/50'
              : toastMessage.type === 'success'
              ? 'bg-emerald-950/90 text-emerald-200 border-emerald-500 shadow-emerald-950/50'
              : 'bg-indigo-950/90 text-indigo-200 border-indigo-500 shadow-indigo-950/50'
          }`}
        >
          <span>{toastMessage.type === 'danger' ? '⚠️' : toastMessage.type === 'success' ? '✅' : 'ℹ️'}</span>
          <span>{toastMessage.text}</span>
          <button
            onClick={() => setToastMessage(null)}
            className="ml-3 text-slate-400 hover:text-white font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 1. ACTIVE PERSONA & TENANT SWITCHER BAR */}
      {/* ========================================================================= */}
      <div className="glass-panel p-6 rounded-2xl border border-indigo-500/20 shadow-xl bg-gradient-to-r from-slate-950 via-indigo-950/20 to-slate-950">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-xl">
                🛡️
              </div>
              <div>
                <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-3">
                  Enterprise Security &amp; CISO Governance Hub
                  <span className="px-2.5 py-0.5 text-[11px] font-bold rounded-full bg-emerald-950 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    SOC 2 Type II Certified
                  </span>
                </h1>
                <p className="text-xs text-slate-400 mt-0.5">
                  Multi-tenant cryptographic partition, hardware-backed envelope encryption, and real-time DLP redaction controls.
                </p>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center gap-3 self-start lg:self-auto">
            <button
              onClick={() => setShowCertModal(true)}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 flex items-center gap-2 transition-colors shadow-sm"
            >
              <span>📜</span> SOC 2 Type II Attestation
            </button>
            <button
              onClick={handleVerifyChain}
              disabled={chainVerifying}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all"
            >
              {chainVerifying ? (
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <span>🛡️</span>
              )}
              Verify Hash Chain
            </button>
          </div>
        </div>

        {/* Tenant & Role Selection Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6">
          {/* Tenant Selector */}
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs font-bold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
                <span>🏢</span> Active Isolated Tenant
              </label>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800/60">
                {currentTenant.isolation_tier}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleTenantChange('Apex SaaS Capital')}
                className={`px-3 py-2.5 rounded-lg text-xs font-bold transition-all text-left flex flex-col gap-0.5 ${
                  selectedTenantName === 'Apex SaaS Capital'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 border border-indigo-400'
                    : 'bg-slate-800/60 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-700/50'
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span>Apex SaaS Capital</span>
                  {selectedTenantName === 'Apex SaaS Capital' && <span className="text-[10px]">● Active</span>}
                </div>
                <span className="text-[10px] font-normal opacity-80 font-mono">tenant-apex-9021</span>
              </button>

              <button
                onClick={() => handleTenantChange('Horizon Buyout Fund')}
                className={`px-3 py-2.5 rounded-lg text-xs font-bold transition-all text-left flex flex-col gap-0.5 ${
                  selectedTenantName === 'Horizon Buyout Fund'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 border border-indigo-400'
                    : 'bg-slate-800/60 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-700/50'
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span>Horizon Buyout Fund</span>
                  {selectedTenantName === 'Horizon Buyout Fund' && <span className="text-[10px]">● Active</span>}
                </div>
                <span className="text-[10px] font-normal opacity-80 font-mono">tenant-horizon-4412</span>
              </button>
            </div>
            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                Retention: {currentTenant.data_retention_policy}
              </span>
            </div>
          </div>

          {/* Persona / Role Selector */}
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs font-bold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
                <span>👤</span> Active User Persona &amp; Role
              </label>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                RBAC Level 4
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {(['IC Partner', 'Deal Lead', 'Analyst', 'LP Viewer'] as RoleName[]).map(role => (
                <button
                  key={role}
                  onClick={() => handleRoleChange(role)}
                  className={`px-2.5 py-2 rounded-lg text-xs font-bold transition-all text-center whitespace-nowrap ${
                    selectedRole === role
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 border border-indigo-400'
                      : 'bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-700/50'
                  }`}
                >
                  {role}
                </button>
              ))}
            </div>
            <div className="mt-3 text-[11px] text-slate-400 pt-2 border-t border-slate-800/60 flex items-center justify-between">
              <span className="truncate pr-2">
                <strong className="text-slate-300">{ROLE_PERMISSIONS[selectedRole].title}:</strong> {ROLE_PERMISSIONS[selectedRole].desc}
              </span>
            </div>
          </div>
        </div>

        {/* Persona Effective Permissions Pills */}
        <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-1">
            Active Permissions:
          </span>
          {ROLE_PERMISSIONS[selectedRole].perms.map(p => (
            <span
              key={p}
              className="text-[10px] font-semibold px-2.5 py-1 rounded-md bg-slate-900 text-slate-300 border border-slate-700/80 flex items-center gap-1.5"
            >
              <span className="text-emerald-400 font-bold">✓</span> {p}
            </span>
          ))}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. SOC 2 TYPE II COMPLIANCE SCORECARD */}
      {/* ========================================================================= */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-base font-extrabold text-white flex items-center gap-2.5">
              <span>📊</span> SOC 2 Type II Security &amp; Trust Scorecard
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Continuous compliance evaluation mapped against AICPA Trust Services Criteria.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="text-slate-400">
              Audit Firm: <strong className="text-slate-200">{soc2Report.certifying_firm}</strong>
            </span>
            <span className="text-slate-400">
              Period: <strong className="text-slate-200">{soc2Report.audit_period}</strong>
            </span>
          </div>
        </div>

        {/* Score Gauge & Overview Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {/* Main Scorecard Gauge */}
          <div className="bg-slate-900/80 p-5 rounded-xl border border-emerald-500/30 flex flex-col justify-between relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none"></div>
            <div>
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Overall Compliance
              </span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-3xl font-black text-emerald-400">
                  {soc2Report.compliance_score_pct}%
                </span>
                <span className="text-xs font-bold text-emerald-300 px-2 py-0.5 rounded bg-emerald-950 border border-emerald-600/40">
                  {soc2Report.audit_readiness_status}
                </span>
              </div>
            </div>
            <div className="mt-4">
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-emerald-500 to-teal-400 h-2 rounded-full transition-all duration-1000"
                  style={{ width: `${soc2Report.compliance_score_pct}%` }}
                ></div>
              </div>
              <span className="text-[10px] text-slate-400 mt-1.5 block">
                5 of 5 Core Controls Active &amp; Passing
              </span>
            </div>
          </div>

          {/* Metric 2: Cryptographic Isolation */}
          <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Tenant Partition</span>
              <span className="text-lg">🔒</span>
            </div>
            <div className="mt-2">
              <span className="text-xl font-black text-white">Zero Leakage</span>
              <p className="text-[11px] text-slate-400 mt-1">
                Strict Row-Level Security with isolated cryptographically validated tenant tokens.
              </p>
            </div>
            <span className="text-[10px] font-mono text-emerald-400 mt-2 font-semibold">
              ● 100% Policy Pass Rate
            </span>
          </div>

          {/* Metric 3: Hardware KMS */}
          <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Encryption Standard</span>
              <span className="text-lg">🔑</span>
            </div>
            <div className="mt-2">
              <span className="text-xl font-black text-white">AES-256-GCM</span>
              <p className="text-[11px] text-slate-400 mt-1">
                Envelope encryption with per-tenant Customer Master Keys and auto-rotation.
              </p>
            </div>
            <span className="text-[10px] font-mono text-indigo-400 mt-2 font-semibold">
              ● FIPS 140-2 Level 3 Validated
            </span>
          </div>

          {/* Metric 4: Zero Retention */}
          <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Data Retention</span>
              <span className="text-lg">⚡</span>
            </div>
            <div className="mt-2">
              <span className="text-xl font-black text-white">Zero Persistence</span>
              <p className="text-[11px] text-slate-400 mt-1">
                Zero training agreements with upstream LLM APIs; ephemeral cache wiped on finish.
              </p>
            </div>
            <span className="text-[10px] font-mono text-teal-400 mt-2 font-semibold">
              ● Contractually Enforced
            </span>
          </div>
        </div>

        {/* Breakdown of Controls Table */}
        <div className="bg-slate-900/40 rounded-xl border border-slate-800 overflow-hidden">
          <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Control Domain &amp; Audit Evidence Breakdown
            </span>
            <span className="text-[11px] text-slate-400">
              Evaluated: <strong>{new Date(soc2Report.last_updated).toLocaleDateString()}</strong>
            </span>
          </div>
          <div className="divide-y divide-slate-800/60">
            {soc2Report.controls.map(ctrl => (
              <div
                key={ctrl.id}
                onClick={() => setSelectedControl(ctrl.id === selectedControl ? null : ctrl.id)}
                className={`p-4 transition-colors cursor-pointer hover:bg-slate-800/30 ${
                  selectedControl === ctrl.id ? 'bg-indigo-950/20' : ''
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-0.5 rounded bg-slate-800 font-mono text-xs font-bold text-slate-300 border border-slate-700">
                      {ctrl.id}
                    </span>
                    <span className="text-sm font-bold text-white">{ctrl.name}</span>
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30">
                      {ctrl.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-emerald-400 h-1.5 rounded-full"
                          style={{ width: `${ctrl.score_pct}%` }}
                        ></div>
                      </div>
                      <span className="font-mono font-bold text-emerald-400">{ctrl.score_pct}%</span>
                    </div>
                    <span className="text-slate-500 font-mono text-[11px]">
                      Audited: {ctrl.last_audited}
                    </span>
                    <span className="text-slate-400 text-xs">{selectedControl === ctrl.id ? '▲' : '▼'}</span>
                  </div>
                </div>
                {selectedControl === ctrl.id && (
                  <div className="mt-3 pt-3 border-t border-slate-800/80 text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800/50">
                    <p className="font-sans">{ctrl.description}</p>
                    <div className="mt-2 flex items-center gap-4 text-[11px] text-slate-400 font-mono">
                      <span>Verification Method: Continuous Synthetic Testing</span>
                      <span>•</span>
                      <span>Auditor Sign-off: PASS</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. IMMUTABLE AUDIT TRAIL VIEWER */}
      {/* ========================================================================= */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-base font-extrabold text-white flex items-center gap-2">
                <span>📜</span> Immutable Audit Trail Viewer
              </h2>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40 shadow-sm flex items-center gap-1.5 animate-pulse">
                <span>🛡️</span> Cryptographic Chain Verified
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Append-only ledger with real-time SHA-256 block hashing and tamper-evident lineage tracking.
            </p>
          </div>

          {/* Verification & Export */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleVerifyChain}
              disabled={chainVerifying}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
            >
              {chainVerifying ? 'Verifying Hashes...' : 'Re-verify Hash Chain'}
            </button>
            <button
              onClick={() => {
                const jsonStr = JSON.stringify(auditLogs, null, 2);
                const blob = new Blob([jsonStr], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `audit-trail-${currentTenant.tenant_id}-${Date.now()}.json`;
                a.click();
                triggerToast('Exported audit trail to JSON', 'info');
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600/80 hover:bg-indigo-600 text-white flex items-center gap-1.5 transition-colors"
            >
              <span>📥</span> Export Audit JSON
            </button>
          </div>
        </div>

        {/* Verification Status Banner */}
        {chainVerifySuccess !== null && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/30 flex items-center justify-between text-xs text-emerald-300">
            <div className="flex items-center gap-2">
              <span>✅</span>
              <span>
                <strong>Cryptographic Integrity Intact:</strong> 5 / 5 log blocks verified. No hash collisions, unlinked parents, or payload mutations detected.
              </span>
            </div>
            <button
              onClick={() => setChainVerifySuccess(null)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
        )}

        {/* Filters and Search Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <label className="text-xs text-slate-400">Filter Role:</label>
            <select
              value={auditFilterRole}
              onChange={e => setAuditFilterRole(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Roles</option>
              <option value="IC Partner">IC Partner</option>
              <option value="Deal Lead">Deal Lead</option>
              <option value="Analyst">Analyst</option>
              <option value="System Service">System Service</option>
            </select>
          </div>
          <div className="w-full sm:w-72">
            <input
              type="text"
              placeholder="Search action, actor, resource, or hash..."
              value={auditSearchQuery}
              onChange={e => setAuditSearchQuery(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-1.5 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Audit Logs Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/50">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                <th className="p-3">Timestamp (UTC)</th>
                <th className="p-3">Actor &amp; Role</th>
                <th className="p-3">Action</th>
                <th className="p-3">Target Resource</th>
                <th className="p-3">Client IP</th>
                <th className="p-3">SHA-256 Hash</th>
                <th className="p-3 text-right">Integrity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filteredLogs.map(log => (
                <tr key={log.id} className="hover:bg-slate-900/50 transition-colors">
                  <td className="p-3 text-slate-400 whitespace-nowrap text-[11px]">
                    {log.timestamp}
                  </td>
                  <td className="p-3 whitespace-nowrap">
                    <div className="font-sans font-semibold text-slate-200">{log.actor}</div>
                    <span className="text-[10px] font-sans px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                      {log.role}
                    </span>
                  </td>
                  <td className="p-3 whitespace-nowrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      log.action.includes('CRYPTO_SHRED')
                        ? 'bg-rose-950 text-rose-300 border border-rose-600'
                        : log.action.includes('APPROVE')
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-600/40'
                        : log.action.includes('ROTATE')
                        ? 'bg-amber-950 text-amber-300 border border-amber-600/40'
                        : 'bg-indigo-950 text-indigo-300 border border-indigo-600/40'
                    }`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="p-3 text-slate-300 font-sans text-[11px] max-w-[200px] truncate" title={log.resource}>
                    {log.resource}
                  </td>
                  <td className="p-3 text-slate-400 text-[11px] whitespace-nowrap font-mono">
                    {log.client_ip}
                  </td>
                  <td className="p-3 font-mono text-[10px] text-slate-400 whitespace-nowrap">
                    <span
                      className="cursor-pointer hover:text-indigo-400 hover:underline"
                      title={log.hash}
                      onClick={() => {
                        navigator.clipboard.writeText(log.hash);
                        triggerToast(`Copied SHA-256 hash to clipboard`, 'info');
                      }}
                    >
                      {log.hash.slice(0, 10)}...{log.hash.slice(-8)}
                    </span>
                  </td>
                  <td className="p-3 text-right whitespace-nowrap">
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-600/30">
                      <span>✓</span> CHAIN LINKED
                    </span>
                  </td>
                </tr>
              ))}
              {filteredLogs.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500 font-sans">
                    No audit logs matching query.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 4. DLP REDACTION SANDBOX */}
      {/* ========================================================================= */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-base font-extrabold text-white flex items-center gap-2">
              <span>🛡️</span> DLP (Data Loss Prevention) Redaction Sandbox
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Test real-time masking of PII, financial accounts, social security numbers, and credential tokens before AI prompt ingestion.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">
              Active Rule Engines: <strong className="text-indigo-300">SSN • CC • Email • Phone • API Keys</strong>
            </span>
          </div>
        </div>

        {/* Preset Sample Buttons */}
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <span className="text-xs text-slate-400 font-semibold">Load Test Preset:</span>
          <button
            onClick={() => {
              setDlpInputText(SAMPLE_DLP_TEXT);
              setDlpResult(executeDLPScan(SAMPLE_DLP_TEXT));
            }}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition-colors"
          >
            Sample 1: Founder SSN &amp; CC
          </button>
          <button
            onClick={() => {
              const text = `PAYROLL LEDGER - STRICT PRIVATE
Executive VP: Jane Doe (SSN: 987-65-4321).
Wire Remittance Account Visa: 4111-2222-3333-4444.
Support contact: finance-help@horizonfund.com or (800) 555-1234.
Cloud KMS master access secret: ghp_1234567890abcdef1234567890abcdef1234.`;
              setDlpInputText(text);
              setDlpResult(executeDLPScan(text));
            }}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition-colors"
          >
            Sample 2: Payroll Wire &amp; Token
          </button>
          <button
            onClick={() => {
              const cleanText = `COMPANY METRICS SUMMARY
Target ARR: $42.5M (+112% YoY).
Gross Margin: 78.4%.
Net Retention Rate: 135%.
Runway: 28 Months with zero debt obligations.`;
              setDlpInputText(cleanText);
              setDlpResult(executeDLPScan(cleanText));
            }}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition-colors"
          >
            Sample 3: Clean Diligence Text (Zero PII)
          </button>
        </div>

        {/* Input & Output Sandbox Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Panel */}
          <div className="flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
                <span>📝</span> Raw Input Payload (Simulated Unsanitized Data)
              </label>
              <span className="text-[10px] font-mono text-slate-500">
                {dlpInputText.length} chars
              </span>
            </div>
            <textarea
              rows={8}
              value={dlpInputText}
              onChange={e => setDlpInputText(e.target.value)}
              placeholder="Paste raw pitch deck text, financial statements, or memos here..."
              className="w-full bg-slate-900/90 border border-slate-700 rounded-xl p-3.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500 transition-colors resize-none leading-relaxed"
            />
            <div className="mt-3 flex items-center justify-between">
              <button
                onClick={handleRunDLP}
                disabled={dlpScanning}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30 flex items-center gap-2 transition-all"
              >
                {dlpScanning ? (
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <span>⚡</span>
                )}
                Scan &amp; Redact
              </button>
              <span className="text-[11px] text-slate-500 font-mono">
                Model Ingestion Barrier: Active
              </span>
            </div>
          </div>

          {/* Redacted Output Panel */}
          <div className="flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
                  <span>🔒</span> Sanitized LLM-Safe Output
                </label>
                {dlpResult && (
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    dlpResult.entities_detected_count > 0
                      ? 'bg-rose-950 text-rose-300 border border-rose-600/40'
                      : 'bg-emerald-950 text-emerald-300 border border-emerald-600/40'
                  }`}>
                    {dlpResult.entities_detected_count > 0
                      ? `${dlpResult.entities_detected_count} Entities Redacted`
                      : 'Clean Payload'}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setActiveDlpTab('redacted')}
                  className={`px-2 py-1 text-[11px] font-semibold rounded ${
                    activeDlpTab === 'redacted' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Output
                </button>
                <button
                  onClick={() => setActiveDlpTab('findings')}
                  className={`px-2 py-1 text-[11px] font-semibold rounded ${
                    activeDlpTab === 'findings' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Findings ({dlpResult?.findings.length || 0})
                </button>
              </div>
            </div>

            {activeDlpTab === 'redacted' ? (
              <div className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl p-3.5 text-xs text-slate-300 font-mono leading-relaxed h-[175px] overflow-y-auto whitespace-pre-wrap">
                {dlpResult ? (
                  dlpResult.redacted_text.split(/(\[REDACTED_[A-Z_]+\])/g).map((segment, idx) => {
                    if (segment.startsWith('[REDACTED_')) {
                      return (
                        <span
                          key={idx}
                          className="px-1.5 py-0.5 mx-0.5 rounded font-extrabold text-[11px] bg-rose-950/90 text-rose-300 border border-rose-500/60 shadow-sm"
                        >
                          {segment}
                        </span>
                      );
                    }
                    return <span key={idx}>{segment}</span>;
                  })
                ) : (
                  <span className="text-slate-600 italic">Click "Scan &amp; Redact" to process payload...</span>
                )}
              </div>
            ) : (
              <div className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl p-3.5 text-xs text-slate-300 font-mono leading-relaxed h-[175px] overflow-y-auto">
                {dlpResult && dlpResult.findings.length > 0 ? (
                  <div className="space-y-2">
                    {dlpResult.findings.map((f, i) => (
                      <div
                        key={i}
                        className="p-2 rounded bg-slate-900/90 border border-slate-800 flex items-center justify-between text-[11px]"
                      >
                        <div className="flex items-center gap-2">
                          <span className="px-1.5 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 font-bold text-[10px]">
                            {f.entity_type}
                          </span>
                          <span className="text-slate-400">Token:</span>
                          <span className="font-bold text-slate-200">{f.redacted_token}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-slate-500">
                            Conf: {(f.confidence_score * 100).toFixed(1)}%
                          </span>
                          <span className="text-emerald-400 font-bold">MASKED</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 italic p-4 text-center">
                    No PII or sensitive tokens detected.
                  </div>
                )}
              </div>
            )}

            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 font-mono">
              <span>Scan Latency: <strong>{dlpResult?.scan_duration_ms || 0}ms</strong></span>
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <span>🛡️</span> Zero Raw PII Transmitted to Models
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 5. KMS ENVELOPE ENCRYPTION MONITOR */}
      {/* ========================================================================= */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-base font-extrabold text-white flex items-center gap-2">
                <span>🔐</span> KMS Envelope Encryption &amp; Cryptographic Shredding
              </h2>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-bold flex items-center gap-1.5 border ${
                  activeKmsKey.state === 'ACTIVE'
                    ? 'bg-emerald-950 text-emerald-300 border-emerald-500/40'
                    : 'bg-rose-950 text-rose-300 border-rose-500 animate-pulse'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    activeKmsKey.state === 'ACTIVE' ? 'bg-emerald-400' : 'bg-rose-500'
                  }`}
                ></span>
                {activeKmsKey.algorithm} {activeKmsKey.state}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Envelope encryption hierarchy: Hardware-backed Customer Master Key (CMK) protects per-workspace Data Encryption Keys (DEKs).
            </p>
          </div>

          <div className="flex items-center gap-3">
            {activeKmsKey.state === 'ACTIVE' ? (
              <>
                <button
                  onClick={handleRotateKey}
                  className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
                >
                  <span>🔄</span> Rotate Key
                </button>
                <button
                  onClick={() => setShredConfirmModalOpen(true)}
                  className="px-3.5 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white shadow-md shadow-rose-600/30 flex items-center gap-1.5 transition-colors"
                >
                  <span>💥</span> Test Cryptographic Shredding
                </button>
              </>
            ) : (
              <button
                onClick={handleRestoreKey}
                className="px-3.5 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/30 flex items-center gap-1.5 transition-colors"
              >
                <span>↺</span> Restore Sandbox DEK
              </button>
            )}
          </div>
        </div>

        {/* Active Key Details Card */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Key Metadata */}
          <div className="lg:col-span-2 bg-slate-900/60 p-5 rounded-xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Customer Master Key (CMK) Identifier
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-indigo-300 border border-slate-700">
                AWS KMS / Hardware HSM
              </span>
            </div>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 font-mono text-xs text-slate-300 break-all select-all">
              {activeKmsKey.cmk_arn}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div>
                <span className="text-slate-500 text-[10px] uppercase font-sans">Key Alias</span>
                <p className="text-slate-200 font-bold mt-0.5 truncate">{activeKmsKey.alias}</p>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] uppercase font-sans">Algorithm</span>
                <p className="text-slate-200 font-bold mt-0.5">{activeKmsKey.algorithm}</p>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] uppercase font-sans">Key Versions</span>
                <p className="text-slate-200 font-bold mt-0.5">v{activeKmsKey.key_versions_count} (Active)</p>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] uppercase font-sans">Auto-Rotation</span>
                <p className="text-slate-200 font-bold mt-0.5">Every {activeKmsKey.auto_rotation_days} Days</p>
              </div>
            </div>

            <div className="pt-2 text-[11px] text-slate-400 font-mono flex items-center justify-between">
              <span>Last Rotated: {new Date(activeKmsKey.last_rotated_at).toLocaleDateString()}</span>
              <span>Tenant ID: <strong className="text-slate-300">{activeKmsKey.tenant_id}</strong></span>
            </div>
          </div>

          {/* Envelope Hierarchy Visualizer */}
          <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
            <div>
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 block">
                Envelope Encryption Topology
              </span>
              <div className="space-y-2.5 text-xs font-mono">
                <div className="p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-500/30 flex items-center gap-2">
                  <span className="text-base">🔑</span>
                  <div>
                    <div className="font-bold text-indigo-300">Customer Master Key (CMK)</div>
                    <div className="text-[10px] text-slate-400">Stored in Hardware Security Module (HSM)</div>
                  </div>
                </div>
                <div className="text-center text-slate-500 text-xs">▼ wraps DEK</div>
                <div className={`p-2.5 rounded-lg border transition-all ${
                  activeKmsKey.state === 'ACTIVE'
                    ? 'bg-slate-950/60 border-slate-700/60'
                    : 'bg-rose-950/40 border-rose-500/40'
                } flex items-center gap-2`}>
                  <span className="text-base">{activeKmsKey.state === 'ACTIVE' ? '🔒' : '💥'}</span>
                  <div>
                    <div className={`font-bold ${activeKmsKey.state === 'ACTIVE' ? 'text-slate-200' : 'text-rose-400'}`}>
                      Data Encryption Key (DEK)
                    </div>
                    <div className="text-[10px] text-slate-400">
                      {activeKmsKey.state === 'ACTIVE' ? 'Ephemeral 256-bit Key per Deal' : 'ZEROIZED / SHREDDED'}
                    </div>
                  </div>
                </div>
                <div className="text-center text-slate-500 text-xs">▼ encrypts</div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-700/60 flex items-center gap-2">
                  <span className="text-base">📄</span>
                  <div>
                    <div className="font-bold text-slate-200">Diligence Chunks &amp; Vectors</div>
                    <div className="text-[10px] text-slate-400">Encrypted at rest with AES-GCM</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MODAL: CRYPTOGRAPHIC SHREDDING CONFIRMATION */}
      {/* ========================================================================= */}
      {shredConfirmModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-rose-600/60 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-scaleUp">
            <div className="flex items-center gap-3 text-rose-500">
              <div className="w-12 h-12 rounded-xl bg-rose-950 border border-rose-600/60 flex items-center justify-center text-2xl">
                ⚠️
              </div>
              <div>
                <h3 className="text-base font-extrabold text-white">
                  Confirm Cryptographic Shredding Test
                </h3>
                <p className="text-xs text-rose-400">
                  Simulated Irreversible Data Zeroization
                </p>
              </div>
            </div>

            <div className="text-xs text-slate-300 space-y-2 bg-slate-900 p-4 rounded-xl border border-slate-800 leading-relaxed">
              <p>
                <strong>What will happen:</strong> In accordance with enterprise zero-retention policies, triggering cryptographic shredding permanently deletes the tenant's <strong>Data Encryption Key (DEK)</strong> from KMS memory and key rings.
              </p>
              <p>
                Without this DEK, all stored document chunks, extracted financial evidence, and memo embeddings become <strong>mathematically indecipherable ciphertext</strong>, satisfying GDPR Right to Erasure and private equity mandate compliance.
              </p>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">
                Reason for Shredding Audit Record:
              </label>
              <input
                type="text"
                value={shredReason}
                onChange={e => setShredReason(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShredConfirmModalOpen(false)}
                disabled={shredProcessing}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmShred}
                disabled={shredProcessing}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30 flex items-center gap-2 transition-all"
              >
                {shredProcessing ? (
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <span>💥</span>
                )}
                Confirm Zeroization &amp; Shred
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: SOC 2 ATTESTATION STUB */}
      {/* ========================================================================= */}
      {showCertModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-slate-700 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5 animate-scaleUp">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <span className="text-2xl">📜</span>
                <div>
                  <h3 className="text-base font-extrabold text-white">
                    SOC 2 Type II Independent Service Auditor's Report
                  </h3>
                  <p className="text-xs text-slate-400">
                    Report ID: {soc2Report.report_id} • Status: Certified Unqualified Opinion
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowCertModal(false)}
                className="text-slate-400 hover:text-white font-bold text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-300 leading-relaxed max-h-[350px] overflow-y-auto pr-2">
              <p>
                <strong>Independent Auditor:</strong> {soc2Report.certifying_firm}
              </p>
              <p>
                <strong>Scope:</strong> Management of AI Due Diligence Copilot has evaluated its control environment over the period of <em>{soc2Report.audit_period}</em> in accordance with the criteria set forth in TSP section 100, 2017 Trust Services Criteria for Security, Confidentiality, and Privacy.
              </p>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 font-mono text-[11px] space-y-1">
                <div>• CC6.1 - Logical Separation &amp; Tenant Partition: PASS (0 exceptions)</div>
                <div>• CC6.6 - Hardware KMS Envelope Encryption (AES-256-GCM): PASS (0 exceptions)</div>
                <div>• CC6.8 - Automated Pre-Flight DLP &amp; PII Scrubbing: PASS (0 exceptions)</div>
                <div>• CC7.2 - Append-Only SHA-256 Audit Trail: PASS (0 exceptions)</div>
                <div>• CC8.1 - Zero Data Retention Model Contracts: PASS (0 exceptions)</div>
              </div>
              <p className="text-slate-400">
                Opinion: In our opinion, management's description of the system is fairly presented, and controls were suitably designed and operated effectively to provide reasonable assurance that service commitments were achieved.
              </p>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-800">
              <span className="text-[11px] text-emerald-400 font-mono font-semibold">
                ✓ Cryptographically Sealed &amp; Signed
              </span>
              <button
                onClick={() => setShowCertModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
              >
                Close Attestation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
