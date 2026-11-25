export type UserRole = 'CITIZEN' | 'ANALYST' | 'VERIFICATION_OFFICER' | 'SECURITY_OFFICER' | 'ADMINISTRATOR';

export type ReportStatus = 'PENDING' | 'TRIAGED' | 'UNDER_REVIEW' | 'VERIFIED' | 'CONTRADICTED' | 'DISMISSED' | 'SUBMITTED';

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
  claim_text: string;
  category: string;
  ai_confidence_score: number;
  ai_analysis_summary?: string | null;
  ai_suggested_status: VerificationDecision | string;
  requires_human_review: boolean;
  verification_decision?: VerificationDecision | null;
  contradicting_document_id?: string | null;
  contradicting_document?: OfficialDocument | null;
  created_at: string;
  updated_at?: string;
}

export interface ReportEvidence {
  id: string;
  file_name: string;
  original_file_name?: string;
  file_type?: string;
  media_type?: string;
  mime_type?: string;
  file_size_bytes: number;
  sha256_hash: string;
  storage_path?: string;
  created_at: string;
}

export interface ReportStatusHistoryItem {
  id: string;
  previous_status: string;
  new_status: string;
  notes?: string | null;
  changed_by_user_id?: string | null;
  created_at: string;
}

export interface Report {
  id: string;
  reference_number: string;
  title: string;
  content_text: string;
  encounter_location?: string | null;
  source_platform: string;
  source_url?: string | null;
  nigerian_state?: string | null;
  incident_date?: string | null;
  status: ReportStatus;
  priority: string;
  submitter_ip_hash?: string | null;
  created_at: string;
  updated_at?: string;
  evidence_items?: ReportEvidence[];
  evidence_files?: ReportEvidence[];
  claims: Claim[];
  status_history?: ReportStatusHistoryItem[];
}

export interface OfficialDocumentVersion {
  version_number: number;
  sha256_hash: string;
  change_summary: string;
  created_at: string;
}

export interface OfficialDocument {
  id: string;
  document_code: string;
  title: string;
  issuing_institution: string;
  summary: string;
  content_text: string;
  content?: string;
  current_version: number;
  sha256_hash: string;
  digital_signature_info?: string | null;
  publication_date: string;
  source_url?: string | null;
  trusted_source_id?: string | null;
  is_authenticated: boolean;
  created_at: string;
  updated_at?: string;
  versions?: OfficialDocumentVersion[];
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
  target_scope: 'NATIONAL' | 'STATE_SPECIFIC' | string;
  target_states?: string[];
  target_state?: string | null;
  debunked_claim_text?: string | null;
  verification_record_id?: string | null;
  official_document_id?: string | null;
  created_at: string;
  published_at?: string | null;
  expires_at?: string | null;
}

export interface ThreatIndicator {
  id: string;
  indicator_type: string;
  evidence_detail: string;
  confidence_score: number;
  created_at: string;
}

export interface ClusterReportSummary {
  report_id: string;
  reference_number: string;
  title: string;
  nigerian_state?: string | null;
  similarity_score: number;
  incident_date?: string | null;
}

export interface NarrativeCluster {
  id: string;
  cluster_title: string;
  cluster_name?: string;
  summary: string;
  core_narrative?: string;
  velocity_score: number;
  propagation_velocity_score?: number;
  amplification_pattern: string;
  threat_level?: string;
  geographic_scope: string[];
  status: string;
  verification_status: string;
  first_reported_at?: string | null;
  last_reported_at?: string | null;
  reports_count: number;
  threat_indicators_count: number;
  created_at: string;
  updated_at: string;
  cluster_reports?: ClusterReportSummary[];
  threat_indicators?: ThreatIndicator[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'CLUSTER' | 'REPORT';
  group?: string | null;
  value: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
  relationship: string;
}

export interface NarrativeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_clusters: number;
  total_connected_reports: number;
}

export interface QueueItem {
  claim_id: string;
  report_id: string;
  report_reference: string;
  claim_text: string;
  category: string;
  ai_confidence_score: number;
  ai_suggested_status: string;
  ai_analysis_summary?: string | null;
  report_priority: string;
  nigerian_state?: string | null;
  incident_date?: string | null;
  created_at: string;
}

export interface VerificationRecord {
  id: string;
  claim_id: string;
  decision: VerificationDecision;
  justification_notes: string;
  public_clarification: string;
  official_document_id?: string | null;
  evidence_sources_consulted?: string[];
  verified_by_user_id: string;
  created_at: string;
  updated_at: string;
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

export interface HashVerificationResult {
  is_official_match: boolean;
  matched_document_code?: string | null;
  issuing_institution?: string | null;
  document_title?: string | null;
  canonical_hash?: string | null;
  submitted_hash: string;
  verification_status: 'EXACT_MATCH' | 'TAMPERED_SUSPECTED' | 'UNREGISTERED' | string;
  analytical_note: string;
}

export interface OfficialSourceMatch {
  document_code?: string;
  title?: string;
  issuing_institution?: string;
  similarity_score: number;
}

export interface ClaimAnalysisResult {
  extracted_claim: string;
  category: string;
  category_confidence: number;
  ai_confidence_score: number;
  ai_suggested_status: string;
  analysis_summary: string;
  contradiction_suspected: boolean;
  sources_consulted: OfficialSourceMatch[];
  recommended_next_action: string;
  requires_human_review: boolean;
  adversarial_injection_detected: boolean;
}

export interface VoiceTranscriptionResult {
  transcript: string;
  detected_language: string;
  confidence: number;
  is_pidgin: boolean;
  duration_seconds?: number;
  service_adapter?: string;
}
