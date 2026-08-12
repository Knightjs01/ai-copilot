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

export interface MfaSetupResponse {
  secret: string;
  provisioning_uri: string;
}

export interface MfaEnableResponse {
  backup_codes: string[];
}

export interface StepUpResponse {
  step_up_token: string;
}

export interface SessionRead {
  id: string;
  user_agent: string | null;
  ip_address: string | null;
  created_at: string;
  last_used_at: string | null;
  is_current: boolean;
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

// Shadow — the anonymous candidate job board. Candidates are a separate principal
// (candidate_auth) with no company_id at all, distinct from the company User/MeResponse above —
// see backend/app/modules/candidate_auth/__init__.py.

export interface CandidateMeResponse {
  id: string;
  email: string;
  full_name: string;
  is_email_verified: boolean;
}

export interface CandidateTokenResponse {
  access_token: string;
  token_type: string;
}

export type CareerIntent =
  | "actively_looking"
  | "open_to_opportunity"
  | "just_exploring"
  | "not_looking";

export type RemotePreference = "remote" | "hybrid" | "onsite" | "flexible";

export type VerificationStatus = "unverified" | "pending" | "verified";

export interface PersonalInfo {
  legal_name: string;
  phone: string | null;
  address: string | null;
}

export interface PersonalInfoInput {
  legal_name: string;
  phone?: string | null;
  address?: string | null;
}

// company_name is the real employer — only ever visible to the owning candidate themselves (via
// GET /phantom-passport/me) or a company after an approved Reveal (see RevealedCareerEntry
// below). Every other view of a career entry (ShadowCareerEntrySummary) shows only the
// anonymized label.
export interface CareerEntry {
  id: string;
  title: string;
  company_name: string;
  company_name_anonymized: string;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  responsibilities: string | null;
  achievements: string[];
}

export interface CareerEntryInput {
  title: string;
  company_name: string;
  company_name_anonymized: string;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  responsibilities?: string | null;
  achievements?: string[];
}

export interface PhantomPassport {
  id: string;
  headline: string | null;
  seniority: string | null;
  years_experience: number | null;
  summary: string | null;
  skills: string[];
  industries: string[];
  location: string | null;
  remote_preference: RemotePreference | null;
  salary_min: number | null;
  salary_max: number | null;
  notice_period: NoticePeriod | null;
  career_intent: CareerIntent;
  verification_status: VerificationStatus;
  completion_percentage: number;
  personal_info: PersonalInfo;
  career_entries: CareerEntry[];
}

export interface PassportUpdateInput {
  headline?: string | null;
  seniority?: string | null;
  years_experience?: number | null;
  summary?: string | null;
  skills: string[];
  industries: string[];
  location?: string | null;
  remote_preference?: RemotePreference | null;
  salary_min?: number | null;
  salary_max?: number | null;
  notice_period?: NoticePeriod | null;
  career_intent?: CareerIntent | null;
  personal_info: PersonalInfoInput;
  career_entries: CareerEntryInput[];
}

export interface CvParseCareerEntry {
  title: string;
  company_name: string;
  company_name_anonymized: string;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  responsibilities: string | null;
  achievements: string[];
}

// A preview only, returned by POST /phantom-passport/parse-cv — nothing here is persisted until
// the candidate reviews it (and can edit it) and saves via PUT /phantom-passport/me.
export interface CvParseResult {
  headline: string | null;
  seniority: string | null;
  years_experience: number | null;
  summary: string | null;
  skills: string[];
  industries: string[];
  career_entries: CvParseCareerEntry[];
  detected_phone: string | null;
  detected_address: string | null;
}

export type EmploymentType = "full_time" | "part_time" | "contract" | "fractional";

export type ShadowJobStatus = "draft" | "published" | "closed";

export type ShadowApplicationStatus =
  | "submitted"
  | "under_review"
  | "reveal_requested"
  | "revealed"
  | "declined"
  | "withdrawn";

// The company-side view of a job posting (own company only, any status) — see
// ShadowJobBoardListing below for the public/candidate-facing view (published only, spans every
// company).
export interface ShadowJob {
  id: string;
  company_id: string;
  project_id: string | null;
  title: string;
  department: string | null;
  seniority: string | null;
  employment_type: EmploymentType;
  location: string | null;
  remote_preference: RemotePreference | null;
  salary_min: number | null;
  salary_max: number | null;
  summary: string;
  description: string;
  requirements: string[];
  status: ShadowJobStatus;
  published_at: string | null;
  applicant_count: number;
}

export interface ShadowJobCreateInput {
  title: string;
  department?: string | null;
  seniority?: string | null;
  employment_type?: EmploymentType;
  location?: string | null;
  remote_preference?: RemotePreference | null;
  salary_min?: number | null;
  salary_max?: number | null;
  summary: string;
  description: string;
  requirements?: string[];
  project_id?: string | null;
}

export type ShadowJobUpdateInput = Partial<Omit<ShadowJobCreateInput, "project_id">>;

// Company identity is shown by name deliberately — Shadow anonymizes the CANDIDATE to the
// recruiter, not the employer to the candidate. See backend shadow_jobs/schemas.py.
export interface ShadowJobBoardListing {
  id: string;
  company_name: string;
  title: string;
  department: string | null;
  seniority: string | null;
  employment_type: EmploymentType;
  location: string | null;
  remote_preference: RemotePreference | null;
  salary_min: number | null;
  salary_max: number | null;
  summary: string;
  description: string;
  requirements: string[];
  published_at: string | null;
}

export interface ShadowApplication {
  id: string;
  shadow_job_id: string;
  job_title: string;
  company_name: string;
  callsign: string;
  status: ShadowApplicationStatus;
  applied_at: string;
}

export interface ShadowCareerEntrySummary {
  title: string;
  company_name_anonymized: string;
  is_current: boolean;
}

// The recruiter-facing anonymized applicant card — deliberately has no field that could hold a
// name, email, phone, or real employer. See backend shadow_jobs/__init__.py.
export interface ShadowProfile {
  application_id: string;
  callsign: string;
  status: ShadowApplicationStatus;
  applied_at: string;
  headline: string | null;
  seniority: string | null;
  years_experience: number | null;
  summary: string | null;
  skills: string[];
  industries: string[];
  location: string | null;
  remote_preference: RemotePreference | null;
  salary_min: number | null;
  salary_max: number | null;
  notice_period: NoticePeriod | null;
  career_intent: CareerIntent;
  career_entries: ShadowCareerEntrySummary[];
}

export type RevealRequestStatus = "pending" | "approved" | "declined";

// The company-side view of a Reveal Request it created.
export interface RevealRequest {
  id: string;
  shadow_application_id: string;
  callsign: string;
  reason: string | null;
  status: RevealRequestStatus;
  requested_at: string;
  responded_at: string | null;
}

// What the candidate sees before deciding — job/company context plus the company's stated
// reason, nothing more.
export interface CandidateRevealRequest {
  id: string;
  shadow_application_id: string;
  job_title: string;
  company_name: string;
  reason: string | null;
  status: RevealRequestStatus;
  requested_at: string;
}

export interface RevealedCareerEntry {
  title: string;
  company_name: string;
  is_current: boolean;
}

// The minimum-necessary disclosure snapshot, only reachable after the candidate has approved a
// Reveal Request. Deliberately excludes the Passport address — see shadow_reveal/__init__.py.
export interface RevealedIdentity {
  application_id: string;
  callsign: string;
  full_name: string;
  email: string;
  phone: string | null;
  career_entries: RevealedCareerEntry[];
  revealed_at: string;
}
