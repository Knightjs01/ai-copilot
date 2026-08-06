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

export interface Candidate {
  id: string;
  company_id: string;
  project_id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  source: CandidateSource;
  status: CandidateStatus;
  resume_original_filename: string | null;
  interview_scheduled_at: string | null;
  prescreen_outcome: PrescreenOutcome | null;
  prescreen_notes: string | null;
  expected_salary: number | null;
  agency_name: string | null;
  current_employer: string | null;
  current_title: string | null;
  location: string | null;
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
  location_breakdown: Record<string, number>;
  notice_period_breakdown: Record<string, number>;
  current_employer_breakdown: Record<string, number>;
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
