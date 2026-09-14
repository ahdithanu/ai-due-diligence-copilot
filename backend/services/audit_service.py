import hashlib
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from backend.domain.schemas import AuditLogRecord


class ImmutableAuditService:
    """
    Append-only Cryptographically Chained SIEM Audit Log Service.
    Each event's entry_hash is computed over:
    f"{prev_hash}:{timestamp}:{actor_id}:{action}:{resource_id}"
    producing an immutable, tamper-evident Merkle/blockchain-style audit trail.
    """

    def __init__(self):
        self._logs: List[AuditLogRecord] = []
        self._seed_initial_audit_trail()

    def _seed_initial_audit_trail(self):
        """Seeds initial system security events into the hash chain."""
        initial_events = [
            ("system-kms", "SYSTEM", "org-apex-capital", "KMS_ROOT_KEY_INIT", "KMS_KEY", "cmk-org-apex-capital", "127.0.0.1"),
            ("sec-admin", "SUPER_ADMIN", "org-apex-capital", "SECURITY_POLICY_BASELINE", "POLICY", "policy-soc2-type2", "192.168.1.100"),
            ("dlp-scanner", "SYSTEM", "org-apex-capital", "DLP_SCANNER_ACTIVE", "SERVICE", "dlp-guard-v1", "127.0.0.1"),
        ]
        for actor_id, actor_role, org_id, action, res_type, res_id, ip in initial_events:
            self.log_event(
                actor_id=actor_id,
                actor_role=actor_role,
                org_id=org_id,
                action=action,
                resource_type=res_type,
                resource_id=res_id,
                client_ip=ip
            )

    def log_event(
        self,
        actor_id: str,
        actor_role: str,
        org_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        client_ip: str = "127.0.0.1"
    ) -> AuditLogRecord:
        """
        Appends an event to the immutable audit log and computes its cryptographic hash.
        Formula:
        entry_hash = hashlib.sha256(f"{prev_hash}:{timestamp}:{actor_id}:{action}:{resource_id}".encode()).hexdigest()
        """
        prev_hash = self._logs[-1].entry_hash if self._logs else "0"
        ts = datetime.now(timezone.utc)
        ts_str = ts.isoformat()
        
        # Compute SHA-256 hash chaining back to previous record
        hash_payload = f"{prev_hash}:{ts_str}:{actor_id}:{action}:{resource_id}".encode("utf-8")
        entry_hash = hashlib.sha256(hash_payload).hexdigest()
        
        record = AuditLogRecord(
            id=str(uuid.uuid4()),
            timestamp=ts,
            actor_id=actor_id,
            actor_role=actor_role,
            org_id=org_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            client_ip=client_ip,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            chain_verified=True
        )
        self._logs.append(record)
        return record

    def list_logs(self, org_id: Optional[str] = None) -> List[AuditLogRecord]:
        """Lists audit log records, optionally filtered by tenant org_id."""
        if org_id:
            return [r for r in self._logs if r.org_id == org_id]
        return list(self._logs)

    def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Verifies the unbroken cryptographic hash-chain across all historical records.
        Returns validation status, total count, genesis and latest hashes, or details of tampering.
        """
        if not self._logs:
            return {
                "chain_valid": True,
                "total_records": 0,
                "genesis_hash": None,
                "latest_hash": None,
                "tampered_index": None
            }
            
        for i, rec in enumerate(self._logs):
            expected_prev = "0" if i == 0 else self._logs[i - 1].entry_hash
            if rec.prev_hash != expected_prev:
                return {
                    "chain_valid": False,
                    "total_records": len(self._logs),
                    "tampered_index": i,
                    "error": f"Previous hash broken at index {i}. Expected {expected_prev}, found {rec.prev_hash}"
                }
                
            ts_str = rec.timestamp.isoformat()
            recomputed_hash = hashlib.sha256(
                f"{rec.prev_hash}:{ts_str}:{rec.actor_id}:{rec.action}:{rec.resource_id}".encode("utf-8")
            ).hexdigest()
            
            if rec.entry_hash != recomputed_hash:
                return {
                    "chain_valid": False,
                    "total_records": len(self._logs),
                    "tampered_index": i,
                    "error": f"Entry hash signature invalid at index {i}."
                }
                
        return {
            "chain_valid": True,
            "total_records": len(self._logs),
            "genesis_hash": self._logs[0].entry_hash,
            "latest_hash": self._logs[-1].entry_hash,
            "tampered_index": None
        }


# Global singleton instance
audit_service = ImmutableAuditService()
