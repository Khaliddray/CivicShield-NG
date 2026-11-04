"""Pydantic schemas for Database Security, Tamper-Evident Auditing, and Incident Response."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AuditLogOut(BaseModel):
    """Immutable audit record entry."""

    id: str
    user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = {}
    sha256_entry_hash: str
    previous_entry_hash: str
    recorded_at: datetime

    model_config = {"from_attributes": True}


class AuditLedgerVerificationResult(BaseModel):
    """Cryptographic ledger verification report."""

    is_valid: bool
    total_entries_verified: int
    first_verified_hash: Optional[str] = None
    latest_verified_hash: Optional[str] = None
    broken_chain_at_id: Optional[str] = None
    verification_message: str


class SecurityEventOut(BaseModel):
    """Security incident monitor record."""

    id: str
    event_type: str
    severity: str
    ip_address: Optional[str] = None
    user_identifier: Optional[str] = None
    details: Optional[dict] = {}
    resolved: bool
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SecurityEventResolveRequest(BaseModel):
    """Payload to resolve an open security incident."""

    resolution_notes: str = Field(min_length=10, description="Mandatory notes on how the security incident was investigated and resolved")


class SecurityMetricsOut(BaseModel):
    """High-level security overview KPIs for the Command Centre."""

    failed_logins_last_24h: int
    currently_locked_accounts: int
    unresolved_security_events: int
    tamper_incidents_detected: int
    total_audit_records_logged: int
    ledger_integrity_status: str  # "VERIFIED_SECURE" or "TAMPER_DETECTED"
