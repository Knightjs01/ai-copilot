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

export type RoleName = "Owner" | "TA Admin" | "Recruiter" | "Hiring Manager" | "Interviewer";

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
  seniority: string | null;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
}

// Resource-level access grant, not a role -- a non-org-wide teammate (e.g. Hiring Manager) can
// only see/act on a project if a row exists here for them. Carries no name/email/role of its own;
// callers cross-reference user_id against the already-fetched team roster (see useTeam()).
export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
}

// A preview only -- nothing here is persisted until saved via PATCH /projects/{id}. See
// CvParseResult for the identical convention this mirrors on the candidate side.
export interface JdUploadResult {
  role_brief: string;
  seniority: string | null;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
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
  // True once at least one Identity Vault reveal event has ever fired for this candidate.
  is_revealed: boolean;
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

export type InterviewKitSourceType = "must_have" | "evaluation_criterion";

export interface InterviewKitQuestion {
  source_type: InterviewKitSourceType;
  source_text: string;
  question_text: string;
  follow_up_prompts: string[];
  included: boolean;
}

export interface InterviewKit {
  id: string;
  project_id: string;
  questions: InterviewKitQuestion[];
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
  industry: string | null;
  years_experience: number | null;
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

// The exact fields a company Owner can choose to reveal from a candidate's Identity Vault, or a
// candidate can choose to disclose when approving a Shadow reveal request. When omitted from a
// reveal/respond call, disclosure_level's tier default applies (matches the pre-existing
// behavior); when given, it's an exact override — see backend app.core.disclosure.
export type IdentityField =
  | "full_name"
  | "email"
  | "phone"
  | "location"
  | "current_employer"
  | "current_title"
  | "linkedin_url"
  | "expected_salary";

export type ShadowField = "full_name" | "email" | "phone" | "career_history";

export type DisclosureLevel = "basic" | "contact" | "full" | "custom";

// The decrypted Reveal Identity response — the only place vault plaintext ever appears in the
// frontend. Never persisted to any query cache beyond the reveal dialog's own local state.
// Fields beyond what disclosed_fields grants are always null, never omitted.
export interface CandidateIdentitySnapshot {
  reveal_event_id: string;
  disclosure_level: DisclosureLevel;
  disclosed_fields: IdentityField[];
  callsign: string;
  candidate_ref: string;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  current_employer: string | null;
  current_title: string | null;
  linkedin_url: string | null;
  expected_salary: number | null;
  original_cv_status: string;
}

// Covers both an ATS-added Candidate and a Shadow marketplace applicant on this project's
// linked Shadow Job -- two different identity systems, merged here so the Vault tab shows every
// real person attached to this project. `source` says which reveal mechanism/route applies.
export type VaultItemSource = "ats" | "shadow";

export interface VaultListItem {
  source: VaultItemSource;
  candidate_id: string | null;
  application_id: string | null;
  shadow_job_id: string | null;
  callsign: string;
  candidate_ref: string | null;
  status: CandidateStatus | ShadowApplicationStatus | string;
  vault_populated: boolean;
}

export interface RevealEventRead {
  id: string;
  source: VaultItemSource;
  candidate_id: string | null;
  application_id: string | null;
  shadow_job_id: string | null;
  callsign: string;
  candidate_ref: string | null;
  actor_email: string;
  reason: string;
  disclosure_level: DisclosureLevel;
  disclosed_fields: string[] | null;
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
  | "reveal_response_needs_review"
  | "needs_interview_arranged"
  | "ready_to_advance"
  | "needs_interview_scheduling"
  | "needs_prescreen"
  | "needs_alignment";

export interface ActionItem {
  type: ActionItemType;
  message: string;
  // Null for a reveal-response item whose Shadow Job isn't linked to a project.
  project_id: string | null;
  project_title: string | null;
  candidate_id: string | null;
  candidate_callsign: string | null;
  // Only set for Shadow-applicant items (reveal_response_needs_review, needs_interview_arranged)
  // -- links straight to the real applicant card, which has no ATS Candidate/project equivalent.
  shadow_job_id: string | null;
  application_id: string | null;
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
  first_name: string;
  last_name: string | null;
  is_email_verified: boolean;
  mfa_enabled: boolean;
}

export interface CandidateMfaSetupResponse {
  secret: string;
  provisioning_uri: string;
}

export interface CandidateMfaEnableResponse {
  backup_codes: string[];
}

export interface CandidateSessionRead {
  id: string;
  user_agent: string | null;
  ip_address: string | null;
  created_at: string;
  last_used_at: string | null;
  is_current: boolean;
}

export interface CandidateTokenResponse {
  access_token: string;
  token_type: string;
}

export interface CandidateMfaChallengeResponse {
  mfa_required: true;
  challenge_token: string;
}

export type CareerIntent =
  | "actively_looking"
  | "open_to_opportunity"
  | "just_exploring"
  | "not_looking";

export type RemotePreference = "remote" | "hybrid" | "onsite" | "flexible";

export type VerificationStatus = "unverified" | "pending" | "verified";

// Controls pre-application discoverability in company-side candidate search. MATCH_ONLY and
// DISCOVERABLE behave identically in that search today (see backend PassportVisibility's
// docstring) -- both included, ranked by AI match. Only PRIVATE is excluded.
export type PassportVisibility = "private" | "match_only" | "discoverable";

export interface PersonalInfo {
  legal_name: string;
  phone: string | null;
}

export interface PersonalInfoInput {
  legal_name: string;
  phone?: string | null;
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
  visibility: PassportVisibility;
  completion_percentage: number;
  // Non-null iff the candidate has approved a Passport Version — see PassportVersionSummary.
  // Nothing is discoverable/usable for applying until this is set.
  current_version_number: number | null;
  // Generated once, at first approval — a stable identity for the Passport itself, distinct
  // from Shadow's per-application callsigns (fresh for every job application, deliberately).
  // Only ever returned to the owning candidate, never surfaced on any company-facing schema.
  callsign: string | null;
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
  visibility?: PassportVisibility | null;
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
  // Field names that are Phantom AI's own normalization rather than text lifted directly from
  // the CV (e.g. "industries", "company_name_anonymized") — everything else with a value is a
  // direct extraction. Drives the "Extracted from your CV" / "Suggested by Phantom AI" badges.
  ai_suggested_fields: string[];
}

export interface CvDocumentStatus {
  original_filename: string;
  content_type: string;
  file_size: number;
  uploaded_at: string;
}

export interface PassportVersionSummary {
  id: string;
  version_number: number;
  approved_at: string;
  source_cv_filename: string | null;
}

// AI co-pilot: on-demand, always returned for the candidate to Apply or Dismiss — never
// silently written to the Passport. See POST /phantom-passport/suggest-summary.
export interface SummaryImprovementRequest {
  headline?: string | null;
  summary: string;
  skills: string[];
}

export interface SummaryImprovementResponse {
  suggested_summary: string;
}

// See POST /phantom-passport/suggest-skills.
export interface SkillsSuggestionRequest {
  headline?: string | null;
  summary?: string | null;
  existing_skills: string[];
}

export interface SkillsSuggestionResponse {
  suggested_skills: string[];
}

// See POST /phantom-passport/suggest-industries.
export interface IndustriesSuggestionRequest {
  headline?: string | null;
  summary?: string | null;
  existing_industries: string[];
}

export interface IndustriesSuggestionResponse {
  suggested_industries: string[];
}

export type EmploymentType = "full_time" | "part_time" | "contract" | "fractional";

export type ShadowJobStatus = "draft" | "pending_review" | "published" | "closed";

export type ShadowApplicationStatus =
  | "submitted"
  | "under_review"
  | "reveal_requested"
  | "revealed"
  | "declined"
  | "withdrawn";

// Recruiter-set hiring-pipeline progress for a Shadow applicant — independent of
// ShadowApplicationStatus above, which tracks identity-reveal workflow state only.
export type ShadowPipelineStage =
  | "new"
  | "screening"
  | "interviewing"
  | "offer"
  | "hired"
  | "rejected";

export type ShadowEffectiveStage = ShadowPipelineStage | "withdrawn";

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
  // null unless the company has opted in to a public profile page -- fails open, no link shown,
  // when a company hasn't opted in.
  company_slug: string | null;
  // Deliberately not gated on company_slug's visibility rule -- employers are always fully
  // visible on Shadow, regardless of whether their full profile page has gone live yet.
  is_verified_employer: boolean;
  logo_url: string | null;
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

// A candidate's private bookmark on a Shadow job board listing. `collection_name` is a
// free-text label ("Dream roles", "Remote") -- no separate collections model, see backend
// saved_shadow_jobs/__init__.py.
export interface SavedShadowJob {
  id: string;
  collection_name: string | null;
  created_at: string;
  job: ShadowJobBoardListing;
}

// A candidate's saved search on the Shadow job board -- notifies by email when a newly
// published job matches (see backend job_alerts/__init__.py). Null criteria fields are
// wildcards; at least one must be set (enforced server-side and mirrored client-side).
export interface JobAlert {
  id: string;
  name: string | null;
  seniority: string | null;
  remote_preference: RemotePreference | null;
  employment_type: EmploymentType | null;
  location: string | null;
  is_active: boolean;
  created_at: string;
}

export interface JobAlertCreateInput {
  name?: string | null;
  seniority?: string | null;
  remote_preference?: RemotePreference | null;
  employment_type?: EmploymentType | null;
  location?: string | null;
}

export interface JobAlertUpdateInput {
  name?: string | null;
  seniority?: string | null;
  remote_preference?: RemotePreference | null;
  employment_type?: EmploymentType | null;
  location?: string | null;
  is_active?: boolean;
}

// Public /phantom-passport/verify/{callsign} shape -- no PII, no personal_info, no career
// history. Confirms a real, approved Phantom Passport exists behind this Callsign; nothing more.
export interface PassportVerification {
  callsign: string;
  headline: string | null;
  seniority: string | null;
  verification_status: VerificationStatus;
  completion_percentage: number;
}

export type CompanySizeBand = "1-10" | "11-50" | "51-200" | "201-500" | "500+";

export type CompanyStatus = "approved" | "suspended";

export type CompanyProfileStatus = "draft" | "pending_review" | "live" | "paused" | "suspended";

export interface ContentItem {
  title: string;
  body: string;
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  email_domain: string;
  is_verified_domain: boolean;
  description: string | null;
  culture: string | null;
  benefits: string[];
  size: CompanySizeBand | null;
  industry: string[];
  logo_url: string | null;
  cover_image_url: string | null;
  hiring_process_overview: string | null;
  profile_status: CompanyProfileStatus;
  status: CompanyStatus;
  tagline: string | null;
  website: string | null;
  founded_year: number | null;
  headquarters: string | null;
  employee_count: number | null;
  is_verified_employer: boolean;
  values: ContentItem[];
  looking_for: string[];
  hiring_highlights: ContentItem[];
}

export interface ProfileStats {
  active_role_count: number;
  total_hires: number;
  // Company.employee_count directly -- a real, company-entered headcount, not a count of
  // Phantom Hire logins. Null until the company fills it in.
  team_size: number | null;
  candidates_in_pipeline: number;
}

export type CommercialPlanCode = "core" | "growth" | "scale";

export interface CommercialPlan {
  id: string;
  code: CommercialPlanCode;
  name: string;
  monthly_price_pence: number;
  annual_price_pence: number;
  active_role_limit: number | null;
  is_active: boolean;
}

export interface CompanyCommercialSummary {
  plan: CommercialPlan | null;
  active_role_count: number;
  effective_limit: number | null;
}

export interface CompanyUpdateInput {
  description?: string | null;
  culture?: string | null;
  benefits?: string[];
  size?: CompanySizeBand | null;
  industry?: string[];
  hiring_process_overview?: string | null;
  tagline?: string | null;
  website?: string | null;
  founded_year?: number | null;
  headquarters?: string | null;
  employee_count?: number | null;
  values?: ContentItem[];
  looking_for?: string[];
  hiring_highlights?: ContentItem[];
}

// Public /companies/{slug} shape (and the self-service preview shape) -- no id/email_domain/
// is_verified_domain/profile_status. is_verified_employer IS included -- the one verification
// signal safe to show a candidate (unlike is_verified_domain, an internal heuristic).
export interface CompanyProfile {
  name: string;
  slug: string;
  description: string | null;
  culture: string | null;
  benefits: string[];
  size: CompanySizeBand | null;
  industry: string[];
  logo_url: string | null;
  cover_image_url: string | null;
  hiring_process_overview: string | null;
  tagline: string | null;
  website: string | null;
  founded_year: number | null;
  headquarters: string | null;
  is_verified_employer: boolean;
  values: ContentItem[];
  looking_for: string[];
  hiring_highlights: ContentItem[];
}

export interface CompanyBoardCard {
  name: string;
  slug: string;
  tagline: string | null;
  logo_url: string | null;
  cover_image_url: string | null;
  industry: string[];
  employee_count: number | null;
  headquarters: string | null;
  is_verified_employer: boolean;
}

export interface ShadowCareerEntrySummary {
  title: string;
  company_name_anonymized: string;
  is_current: boolean;
  start_date: string | null;
  end_date: string | null;
  responsibilities: string | null;
  achievements: string[];
}

export type MatchTier = "Excellent Match" | "Strong Match" | "Potential Match" | "Weak Match";
export type DimensionRatingValue = "Strong" | "Moderate" | "Weak";

// One real, evidence-backed dimension of a match -- Role alignment/Industry experience/Functional
// experience come from the LLM's own forced-tool-call response; Seniority/Location/Compensation
// are computed deterministically from data already on file. Never a bare label -- `evidence`
// always names the real values compared. See backend passport_matching/schemas.py::DimensionRating.
export interface DimensionRating {
  dimension: string;
  rating: DimensionRatingValue;
  evidence: string;
}

// A real, cached AI match score between the candidate's approved Passport and one job. Kept
// separate from ShadowJobBoardListing (mirrors how SavedShadowJob wraps a `job:` field rather
// than mutating the base listing type) -- the public board stays auth-agnostic, computed match
// data lives in its own fetch. See backend passport_matching/schemas.py.
export interface ShadowJobMatch {
  job_id: string;
  match_tier: MatchTier;
  match_score: number;
  strengths: string[];
  gaps: string[];
  summary: string;
  dimension_breakdown: DimensionRating[];
  generated_at: string;
}

// See backend shadow_jobs/schemas.py::SalaryBenchmark/ViewTimeBenchmark/JobIntelligence. Real
// aggregations, gated on a minimum sample size -- has_enough_data is false far more often than
// not for a young product, and that's the honest, expected common case, not a bug.
export interface SalaryBenchmark {
  has_enough_data: boolean;
  sample_size: number;
  company_count: number;
  median: number | null;
  this_job_vs_median: "above" | "at" | "below" | null;
}

export interface ViewTimeBenchmark {
  has_enough_data: boolean;
  sample_size: number;
  median_hours: number | null;
}

export interface JobIntelligence {
  salary_benchmark: SalaryBenchmark;
  view_time_benchmark: ViewTimeBenchmark;
}

// Why a recruiter passed on a candidate -- see backend passport_matching/schemas.py::PassReason.
export type PassReason =
  | "insufficient_experience"
  | "too_senior"
  | "too_junior"
  | "wrong_sector"
  | "wrong_location"
  | "compensation_mismatch"
  | "skills_mismatch"
  | "not_relevant"
  | "already_engaged"
  | "role_filled"
  | "other";

// This company's real, computed relationship with this candidate -- priority order
// currently_engaged > in_talent_pool > introduction_pending > previously_passed >
// previously_applied > introduction_declined > new. See backend
// passport_matching/schemas.py::RelationshipStatus.
export type RelationshipStatus =
  | "new"
  | "previously_applied"
  | "previously_passed"
  | "in_talent_pool"
  | "currently_engaged"
  | "introduction_pending"
  | "introduction_declined";

// One discoverable candidate ranked against a company's job — see backend
// passport_matching/schemas.py::CandidateSearchResult. No PII field, same discipline as
// ShadowProfile. `match_summary` (not `summary`) to avoid colliding with the passport's own bio.
export interface CandidateSearchResult {
  callsign: string;
  headline: string | null;
  seniority: string | null;
  years_experience: number | null;
  summary: string | null;
  skills: string[];
  industries: string[];
  location: string | null;
  remote_preference: string | null;
  salary_min: number | null;
  salary_max: number | null;
  notice_period: string | null;
  career_intent: string;
  career_entries: ShadowCareerEntrySummary[];
  match_tier: MatchTier;
  match_score: number;
  match_summary: string;
  strengths: string[];
  gaps: string[];
  dimension_breakdown: DimensionRating[];
  relationship_status: RelationshipStatus;
}

export type IntroductionRequestStatus = "pending" | "accepted" | "declined";

// Company-side view of one Request Introduction it sent. See backend
// shadow_introduction/schemas.py::IntroductionRequestRead.
export interface IntroductionRequestRead {
  id: string;
  callsign: string;
  shadow_job_id: string;
  message: string | null;
  status: IntroductionRequestStatus;
  requested_at: string;
  responded_at: string | null;
  resulting_application_id: string | null;
}

// The candidate's own view of a Request Introduction -- real company name/job title, since this
// product's anonymity protects the candidate's identity from the recruiter, not the other way
// around. See backend shadow_introduction/schemas.py::CandidateIntroductionRequestRead.
export interface CandidateIntroductionRequestRead {
  id: string;
  company_name: string;
  job_title: string;
  message: string | null;
  status: IntroductionRequestStatus;
  requested_at: string;
  responded_at: string | null;
  resulting_application_id: string | null;
}

// A Talent Pool candidate ranked against a NEW role -- same shape as CandidateSearchResult, plus
// the grant context that makes the result meaningful ("previously considered for X"). See
// backend passport_matching/schemas.py::TalentPoolMatchResult.
export interface TalentPoolMatchResult extends CandidateSearchResult {
  source_role_title: string;
  scope: TalentPoolScope;
  granted_at: string;
}

// The candidate's own view of a real match a company computed against their Talent Pool grant --
// not anonymized (this is the candidate looking at their own data), with a real, still-applyable
// job to view/apply to. See backend passport_matching/schemas.py::TalentPoolOpportunity.
export interface TalentPoolOpportunity {
  job_id: string;
  job_title: string;
  company_name: string;
  match_tier: MatchTier;
  match_score: number;
  match_summary: string;
  strengths: string[];
  gaps: string[];
  dimension_breakdown: DimensionRating[];
  generated_at: string;
}

export interface BoardFilters {
  seniority: string | null;
  remote_preference: string | null;
  employment_type: string | null;
  location: string | null;
}

// The Phantom AI co-pilot -- a scoped, tool-calling assistant, not an open chat. `context_type`
// tells the backend what the candidate is currently looking at so it can route accurately
// without ever being given (or having to guess) an ID. See backend copilot/schemas.py.
export type CopilotContextType = "job" | "application" | "interview" | "passport" | "none";

export type CopilotAction =
  | "search_jobs"
  | "explain_match"
  | "suggest_improvements"
  | "summarize_applications"
  | "interview_prep"
  | "reply";

export interface CopilotMessage {
  role: "user" | "assistant";
  content: string;
}

export interface CopilotChatRequest {
  message: string;
  context_type: CopilotContextType;
  context_id?: string | null;
  history: CopilotMessage[];
}

export interface CopilotChatResponse {
  reply: string;
  action: CopilotAction;
  board_filters: BoardFilters | null;
  match: ShadowJobMatch | null;
  suggested_summary: string | null;
  interview_prep_questions: string[] | null;
}

// The recruiter-facing applicant card — anonymous (callsign only) until the candidate reveals
// their identity for this specific application, at which point revealed_full_name/_email/_phone
// (and, when career history was part of the disclosure, revealed_career_entries) populate and
// stay populated (never re-anonymized). career_entries itself always stays anonymized.
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
  unread_message_count: number;
  has_upcoming_interview: boolean;
  // Null when no Talent Pool request has ever been made for this candidate at this company.
  talent_pool_status: TalentPoolGrantStatus | null;
  pipeline_stage: ShadowPipelineStage;
  // pipeline_stage, unless the candidate has withdrawn — withdrawal always overrides wherever
  // the application sat in the pipeline. This is the field the merged Kanban groups by.
  effective_stage: ShadowEffectiveStage;
  // True until a recruiter opens this applicant's card for the first time.
  is_new: boolean;
  // True when the candidate has responded (approved/declined) to a reveal request and nobody's
  // opened this applicant's card since. Independent of is_new.
  reveal_response_is_new: boolean;
  // Populated exactly once, at first successful identity reveal -- the single authoritative
  // source every surface (Kanban, applicant list, workspace, Passport, messages, interviews)
  // reads from afterward. Null until revealed, or if that field wasn't part of the disclosure.
  revealed_full_name: string | null;
  revealed_email: string | null;
  revealed_phone: string | null;
  // Same one-time-persist pattern as the three fields above -- real employer names, populated
  // only when career history was part of the approved disclosure.
  revealed_career_entries: RevealedCareerEntry[] | null;
}

// Same shape as ShadowProfile, plus which job/project this application belongs to -- powers the
// company-wide Candidates/Pipeline merge, where the job context isn't already known from the URL.
export interface ShadowProfileCompanyWide extends ShadowProfile {
  shadow_job_id: string;
  job_title: string;
  project_id: string | null;
}

// Real audit trail entry for one applicant -- see backend audit/schemas.py::AuditEntryRead.
// actor_email is null for candidate-initiated actions (reveal response, application withdrawal).
export interface AuditEntry {
  id: string;
  actor_email: string | null;
  action: string;
  target_type: string;
  target_id: string | null;
  extra_data: Record<string, unknown>;
  created_at: string;
}

// A private, recruiter-team-only note on a Shadow applicant -- never candidate-visible. See
// backend applicant_notes/schemas.py.
export interface ApplicantNote {
  id: string;
  author_user_id: string;
  author_email: string;
  body: string;
  created_at: string;
}

export type MessageSenderType = "company" | "candidate";

// is_mine/sender_label are resolved server-side per the requesting principal -- the frontend
// never has to guess who's who. See backend messages/schemas.py.
export interface Message {
  id: string;
  sender_type: MessageSenderType;
  sender_label: string;
  body: string;
  created_at: string;
  is_mine: boolean;
}

export interface MessageThread {
  application_id: string;
  messages: Message[];
}

// One row in either side's thread list/inbox.
export interface MessageThreadSummary {
  application_id: string;
  job_title: string;
  company_name: string;
  callsign: string;
  last_message_preview: string | null;
  last_message_at: string | null;
  unread_count: number;
}

export type InterviewStatus = "scheduled" | "cancelled" | "completed";

export interface Interview {
  id: string;
  application_id: string;
  scheduled_at: string;
  location: string | null;
  meeting_link: string | null;
  status: InterviewStatus;
  created_at: string;
  interviewer_user_ids: string[];
}

// The candidate's flat "My Interviews" list embeds job/company/callsign context so the portal
// never needs a per-application drill-down. See backend interviews/schemas.py.
export interface CandidateInterviewSummary extends Interview {
  job_title: string;
  company_name: string;
  callsign: string;
}

// Company-wide "Interviews" nav destination -- omits company_name (every row is already this
// company's own). project_id lets a row deep-link into a linked Project's Interviews tab;
// shadow_job_id is always present and is what actually powers this interview's own detail page.
export interface CompanyInterviewSummary extends Interview {
  job_title: string;
  callsign: string;
  project_id: string | null;
  shadow_job_id: string;
}

export interface ProjectActivityEntry {
  id: string;
  action: string;
  actor_user_id: string | null;
  extra_data: Record<string, unknown>;
  created_at: string;
}

export type CompetencyRating = "Strong" | "Moderate" | "Weak";
export type OverallRecommendation = "Strong Hire" | "Hire" | "No Hire" | "Strong No Hire";

export interface CompetencyScore {
  competency: string;
  rating: CompetencyRating;
  evidence: string;
}

// A generated-but-not-yet-saved preview -- nothing is persisted until an explicit Save call.
export interface InterviewScorecardDraft {
  competency_scores: CompetencyScore[];
  overall_recommendation: OverallRecommendation;
  summary: string;
}

export interface InterviewScorecard {
  id: string;
  interview_id: string;
  submitted_by_user_id: string;
  notes: string;
  competency_scores: CompetencyScore[];
  overall_recommendation: OverallRecommendation;
  model_used: string;
  generated_at: string;
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

// One row in the candidate-wide "Identity Activity" timeline -- spans every application, unlike
// CandidateRevealRequest which is scoped to one. disclosure_level/disclosed_fields are null
// while pending/declined; disclosed_fields specifically stays null even when approved unless the
// candidate explicitly narrowed disclosure (a routine full approval only sets disclosure_level).
export interface CandidateRevealHistoryItem {
  id: string;
  shadow_application_id: string;
  job_title: string;
  company_name: string;
  reason: string | null;
  status: RevealRequestStatus;
  requested_at: string;
  responded_at: string | null;
  disclosure_level: DisclosureLevel | null;
  disclosed_fields: ShadowField[] | null;
}

export type TalentPoolGrantStatus = "requested" | "granted" | "declined" | "withdrawn";
export type TalentPoolScope = "project_only" | "company_wide";

// Company-side view of one grant it created. callsign is populated only once status == "granted"
// -- see backend phantom_passport/models.py's documented exception for PhantomPassport.callsign.
export interface TalentPoolGrantRead {
  id: string;
  shadow_application_id: string | null;
  source_role_title: string;
  status: TalentPoolGrantStatus;
  scope: TalentPoolScope;
  requested_at: string;
  responded_at: string | null;
  review_date: string | null;
  callsign: string | null;
}

// One row in the company's Talent Pool list -- only ever built from a granted row.
export interface TalentPoolPoolListItem {
  id: string;
  callsign: string;
  headline: string | null;
  seniority: string | null;
  source_role_title: string;
  scope: TalentPoolScope;
  granted_at: string;
  // Company-only organizational label (Phase 4) -- null means ungrouped. See backend
  // TalentPoolGrant.pool_name's docstring for why this isn't a separate entity.
  pool_name: string | null;
}

// Bulk Talent Pool request from Search Candidates results -- see backend
// talent_pool/schemas.py::TalentPoolBulkRequestResult.
export interface TalentPoolBulkSkip {
  callsign: string;
  reason: string;
}

export interface TalentPoolBulkRequestResult {
  requested: string[];
  skipped: TalentPoolBulkSkip[];
}

// What the candidate sees -- company/role context plus the company's optional note.
export interface CandidateTalentPoolRequest {
  id: string;
  company_name: string;
  source_role_title: string;
  note: string | null;
  status: TalentPoolGrantStatus;
  scope: TalentPoolScope;
  requested_at: string;
  responded_at: string | null;
  review_date: string | null;
}

export interface RevealedCareerEntry {
  title: string;
  company_name: string;
  is_current: boolean;
  start_date: string | null;
  end_date: string | null;
  responsibilities: string | null;
  achievements: string[];
}

// The minimum-necessary disclosure snapshot, only reachable after the candidate has approved a
// Reveal Request. Deliberately excludes the Passport address — see shadow_reveal/__init__.py.
export interface RevealedIdentity {
  application_id: string;
  disclosure_level: DisclosureLevel;
  disclosed_fields: ShadowField[];
  callsign: string;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  career_entries: RevealedCareerEntry[];
  revealed_at: string;
}

// Phantom internal staff -- a third, separate principal from company Users and candidates. See
// backend platform_admin/__init__.py.
export interface PlatformAdmin {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  permissions: string[];
  mfa_enabled: boolean;
}

export type PlatformAdminRoleName =
  | "Super Admin"
  | "Platform Admin"
  | "Reviewer"
  | "Support Admin"
  | "Analytics";

export interface PlatformAdminSummary {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  roles: string[];
  created_at: string;
}

export interface AdminShadowJob extends ShadowJob {
  company_name: string;
}

export interface LocationSuggestion {
  formatted: string;
  city: string | null;
  country: string | null;
  lat: number;
  lon: number;
}

export type AccessRequestStatus = "pending" | "approved" | "rejected";

// The employer access-request queue -- the replacement for self-service company signup. See
// backend company_access/__init__.py.
export interface CompanyAccessRequest {
  id: string;
  full_name: string;
  job_title: string | null;
  company_name: string;
  work_email: string;
  status: AccessRequestStatus;
  created_at: string;
}

export interface AccessRequestStats {
  pending_requests: number;
  approved_requests: number;
  rejected_requests: number;
  active_companies: number;
  suspended_companies: number;
  active_role_count: number;
  verified_candidate_count: number;
  application_count: number;
}

export type ActionQueueItemType = "access_request" | "job_review" | "profile_review";

export interface ActionQueueItem {
  id: string;
  type: ActionQueueItemType;
  title: string;
  subtitle: string;
  company_name: string;
  created_at: string;
  priority: "high" | "normal";
  url: string;
}

// The admin-facing company directory row -- leaner than the owning company's own Company shape,
// includes admin-only fields (user_count) never returned to a company's own users.
export interface AdminCompanySummary {
  id: string;
  name: string;
  slug: string;
  email_domain: string;
  is_verified_domain: boolean;
  status: CompanyStatus;
  profile_status: CompanyProfileStatus;
  user_count: number;
  created_at: string;
  commercial_plan_code: CommercialPlanCode | null;
  active_role_limit_override: number | null;
  is_verified_employer: boolean;
}

export interface PlatformAdminAuditLogEntry {
  id: string;
  admin_id: string;
  action: string;
  target_type: string;
  target_id: string | null;
  extra_data: Record<string, unknown>;
  created_at: string;
}

// --- Candidate Activity (Phase 5) — see backend candidate_activity/schemas.py -----------------

export type TimelineEventType =
  | "application_submitted"
  | "reveal_requested"
  | "reveal_responded"
  | "talent_pool_requested"
  | "talent_pool_responded"
  | "talent_pool_withdrawn"
  | "passed"
  | "introduction_requested"
  | "introduction_responded"
  | "conversation_started";

// `description` is always a short, plain-language summary built server-side -- never raw
// message content, even for the company's own conversations. `callsign` is populated only on
// the company-wide feed (useRecentActivity); the per-candidate timeline caller already knows
// who they're looking at.
export interface TimelineEntry {
  event_type: TimelineEventType;
  description: string;
  occurred_at: string;
  callsign: string | null;
}

export interface RediscoveryCandidate {
  callsign: string;
  headline: string | null;
  seniority: string | null;
  changes: string[];
  passed_reason: PassReason | null;
  passed_shadow_job_id: string | null;
  passed_for_job_title: string | null;
  passed_at: string;
}

export interface AiRecommendation {
  job_id: string;
  job_title: string;
  callsign: string;
  match_tier: MatchTier;
  match_score: number;
  match_summary: string;
}
