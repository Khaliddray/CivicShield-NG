export type UserRole = 'CITIZEN' | 'ANALYST' | 'VERIFICATION_OFFICER' | 'SECURITY_OFFICER' | 'ADMINISTRATOR';

export type ReportStatus = 'PENDING' | 'TRIAGED' | 'UNDER_REVIEW' | 'VERIFIED' | 'CONTRADICTED' | 'DISMISSED';

export type VerificationDecision = 'UNVERIFIED' | 'UNDER_REVIEW' | 'VERIFIED' | 'CONTRADICTED' | 'INSUFFICIENT_EVIDENCE' | 'WITHDRAWN';

export type AlertSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'INFORMATIONAL';

export type AlertStatus = 'DRAFT' | 'PENDING_APPROVAL' | 'PUBLISHED' | 'EXPIRED' | 'WITHDRAWN';

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone_number?: string | null;
  state_of_residence?: string | null;
  roles: UserRole[];
  permissions: string[];
  is_active: boolean;
  is_verified: boolean;
}

export interface Claim {
  id: string;
  report_id: string;
  extracted_claim: string;
  category: string;
  ai_confidence_score: number;
  ai_analysis_summary: string;
  ai_suggested_status: VerificationDecision;
  requires_human_review: boolean;
  verification_decision?: VerificationDecision | null;
  contradicting_document_id?: string | null;
  contradicting_document?: OfficialDocument | null;
  created_at: string;
}

export interface ReportEvidence {
  id: string;
  file_name: string;
  media_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  created_at: string;
}

export interface Report {
  id: string;
  reference_number: string;
  content_text: string;
  source_platform: string;
  source_url?: string | null;
  nigerian_state?: string | null;
  status: ReportStatus;
  priority: string;
  ai_triage_score: number;
  is_anonymously_submitted: boolean;
  created_at: string;
  evidence_files: ReportEvidence[];
  claims: Claim[];
}

export interface OfficialDocument {
  id: string;
  document_code: string;
  title: string;
  issuing_institution: string;
  content: string;
  summary: string;
  publication_date: string;
  sha256_hash: string;
  current_version: number;
  source_url?: string | null;
  created_at: string;
}

export interface Alert {
  id: string;
  alert_reference: string;
  title: string;
  summary: string;
  full_clarification: string;
  severity: AlertSeverity;
  category: string;
  status: AlertStatus;
  target_scope: string;
  target_state?: string | null;
  debunked_claim_text?: string | null;
  official_document_id?: string | null;
  created_at: string;
  published_at?: string | null;
}

export interface NarrativeCluster {
  id: string;
  cluster_name: string;
  core_narrative: string;
  primary_category: string;
  target_entity?: string | null;
  threat_level: string;
  propagation_velocity_score: number;
  report_count: number;
  unique_sources_count: number;
  distinct_states_count: number;
  geographical_spread?: string[] | null;
  first_detected_at: string;
  last_activity_at: string;
  reports?: Report[];
}

export interface AuditLog {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  user_id?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
  details?: Record<string, unknown> | null;
  sha256_entry_hash: string;
  previous_entry_hash: string;
  recorded_at: string;
}

export interface AuditLedgerResult {
  is_valid: boolean;
  total_entries_verified: number;
  broken_chain_at_id?: string | null;
  first_verified_hash?: string | null;
  latest_verified_hash?: string | null;
  verification_message: string;
}

export interface SecurityEvent {
  id: string;
  event_type: string;
  severity: string;
  ip_address?: string | null;
  user_identifier?: string | null;
  details?: Record<string, unknown> | null;
  resolved: boolean;
  resolved_at?: string | null;
  resolution_notes?: string | null;
  created_at: string;
}

export interface SecurityMetrics {
  total_audit_records: number;
  active_threat_events: number;
  tamper_incidents_recorded: number;
  brute_force_attempts_blocked: number;
  ledger_integrity_status: string;
}
