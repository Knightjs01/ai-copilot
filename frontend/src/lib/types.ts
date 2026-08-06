// Mirrors backend/app/modules/*/schemas.py Read/Create/Update models. Keep in sync by hand —
// no codegen pipeline exists yet.

export type ProjectStatus = "draft" | "open" | "on_hold" | "filled" | "cancelled";

export type CandidateSource = "referral" | "job_board" | "agency" | "direct" | "other";

export type CandidateStatus =
  | "new"
  | "screening"
  | "interviewing"
  | "offer"
  | "hired"
  | "rejected"
  | "withdrawn";

export type PrescreenOutcome = "advance" | "reject" | "hold";

export type NoticePeriod =
  | "immediate"
  | "one_week"
  | "two_weeks"
  | "one_month"
  | "two_months"
  | "three_plus_months";

export type RoleName = "Owner" | "Admin" | "Member";

export interface UserRead {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_email_verified: boolean;
  roles: string[];
}

export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  company_id: string;
  is_email_verified: boolean;
  mfa_enabled: boolean;
  roles: string[];
  permissions: string[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface MfaChallengeResponse {
  mfa_required: true;
  challenge_token: string;
}

export interface Project {
  id: string;
  company_id: string;
  title: string;
  department: string | null;
  status: ProjectStatus;
  hiring_manager_id: string | null;
  created_by_id: string;
  role_brief: string | null;
}

// Real name/email/phone/location/current_employer/current_title never appear on this type — they
// live exclusively in the Identity Vault (see CandidateIdentitySnapshot below), revealed only via
// the Owner-gated reveal flow. Every other view of a candidate uses callsign/candidate_ref.
export interface Candidate {
  id: string;
  company_id: string;
  project_id: string;
  callsign: string;
  candidate_ref: string;
  source: CandidateSource;
  status: CandidateStatus;
  resume_original_filename: string | null;
  interview_scheduled_at: string | null;
  prescreen_outcome: PrescreenOutcome | null;
  prescreen_notes: string | null;
  expected_salary: number | null;
  agency_name: string | null;
  notice_period: NoticePeriod | null;
  created_by_id: string;
}

export interface SalaryStats {
  count: number;
  average: number | null;
  minimum: number | null;
  maximum: number | null;
}

export interface ProjectAnalytics {
  total_candidates: number;
  status_breakdown: Record<string, number>;
  prescreen_outcome_breakdown: Record<string, number>;
  fit_rating_breakdown: Record<string, number>;
  source_breakdown: Record<string, number>;
  agency_breakdown: Record<string, number>;
  salary_stats: SalaryStats;
  notice_period_breakdown: Record<string, number>;
}

export interface SanitizedProfile {
  id: string;
  candidate_id: string;
  redacted_text: string;
}

export interface HiringBlueprint {
  id: string;
  project_id: string;
  role_summary: string;
  key_responsibilities: string[];
  must_have_qualifications: string[];
  nice_to_have_qualifications: string[];
  evaluation_criteria: string[];
  model_used: string;
  generated_at: string;
}

export interface HiringManagerAlignment {
  id: string;
  project_id: string;
  top_requirements: string[];
  submitted_by_id: string;
  submitted_at: string;
}

export interface EducationEntry {
  institution: string;
  degree: string;
  field: string;
}

export interface IntelligencePack {
  id: string;
  candidate_id: string;
  skills: string[];
  experience_summary: string;
  education: EducationEntry[];
  narrative_summary: string;
  highlights: string[];
  model_used: string;
  generated_at: string;
}

export type FitRating = "Strong Fit" | "Good Fit" | "Possible Fit" | "Weak Fit";

export interface PrescreenAssessment {
  id: string;
  candidate_id: string;
  fit_rating: FitRating;
  fit_summary: string;
  strengths: string[];
  gaps: string[];
  suggested_questions: string[];
  areas_to_probe: string[];
  handoff_recommendations: string[] | null;
  model_used: string;
  generated_at: string;
}

export type RevealReason =
  | "Hiring Manager Interview"
  | "Offer Preparation"
  | "Background Checks"
  | "Client Submission"
  | "Hiring Manager Review"
  | "Other";

// The decrypted Reveal Identity response — the only place vault plaintext ever appears in the
// frontend. Never persisted to any query cache beyond the reveal dialog's own local state.
export interface CandidateIdentitySnapshot {
  reveal_event_id: string;
  callsign: string;
  candidate_ref: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  location: string | null;
  current_employer: string | null;
  current_title: string | null;
  linkedin_url: string | null;
  expected_salary: number | null;
  original_cv_status: string;
}

export interface VaultListItem {
  candidate_id: string;
  callsign: string;
  candidate_ref: string;
  status: CandidateStatus;
  vault_populated: boolean;
}

export interface RevealEventRead {
  id: string;
  candidate_id: string;
  callsign: string;
  candidate_ref: string;
  actor_email: string;
  reason: string;
  revealed_at: string;
  closed_at: string | null;
  duration_seconds: number | null;
}

export interface VaultDashboardStats {
  total_candidates: number;
  active_vault_records: number;
  reveal_event_count: number;
  recent_reveals: RevealEventRead[];
}

export interface PurgeCertificate {
  project_title: string;
  candidate_count: number;
  data_categories_destroyed: string[];
  purged_at: string;
}

export type ActionItemType =
  | "ready_to_advance"
  | "needs_interview_scheduling"
  | "needs_prescreen"
  | "needs_alignment";

export interface ActionItem {
  type: ActionItemType;
  message: string;
  project_id: string;
  project_title: string;
  candidate_id: string | null;
  candidate_callsign: string | null;
}

export interface DashboardStats {
  live_projects: number;
  candidates_in_process: number;
  prescreen_stage_count: number;
  hiring_manager_stage_count: number;
  action_item_count: number;
  action_items: ActionItem[];
}

export interface PurgedProjectRecord {
  id: string;
  project_id: string;
  project_title: string;
  candidate_count: number;
  data_categories_destroyed: string[];
  purged_by_email: string;
  purged_at: string;
}

export interface AuditLogEntry {
  id: string;
  actor_email: string | null;
  action: string;
  target_type: string;
  target_id: string | null;
  extra_data: Record<string, unknown>;
  created_at: string;
}

export interface HistoricVaultOverview {
  purged_project_count: number;
  purged_projects: PurgedProjectRecord[];
  recent_audit_entries: AuditLogEntry[];
}
