import type { BadgeProps } from "@/components/ui/badge";
import type {
  CandidateSource,
  CandidateStatus,
  CareerIntent,
  CompanySizeBand,
  EmploymentType,
  FitRating,
  InterviewStatus,
  MatchTier,
  NoticePeriod,
  PassportVisibility,
  PrescreenOutcome,
  ProjectStatus,
  RemotePreference,
  RoleName,
  ShadowApplicationStatus,
  ShadowField,
  ShadowJobStatus,
  VerificationStatus,
} from "@/lib/types";

type Variant = NonNullable<BadgeProps["variant"]>;

export const ROLE_LABEL: Record<RoleName, string> = {
  Owner: "Owner",
  Admin: "Admin",
  Member: "Member",
};

export const ROLE_VARIANT: Record<RoleName, Variant> = {
  Owner: "success",
  Admin: "info",
  Member: "neutral",
};

export const PROJECT_STATUS_LABEL: Record<ProjectStatus, string> = {
  draft: "Draft",
  open: "Open",
  on_hold: "On hold",
  filled: "Filled",
  cancelled: "Cancelled",
};

export const PROJECT_STATUS_VARIANT: Record<ProjectStatus, Variant> = {
  draft: "neutral",
  open: "info",
  on_hold: "warning",
  filled: "success",
  cancelled: "outline",
};

export const CANDIDATE_STATUS_LABEL: Record<CandidateStatus, string> = {
  new: "New",
  screening: "Screening",
  interviewing: "Interviewing",
  offer: "Offer",
  hired: "Hired",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

// Column order for the pipeline Kanban board.
export const CANDIDATE_STATUS_COLUMNS: CandidateStatus[] = [
  "new",
  "screening",
  "interviewing",
  "offer",
  "hired",
  "rejected",
  "withdrawn",
];

export const CANDIDATE_STATUS_VARIANT: Record<CandidateStatus, Variant> = {
  new: "neutral",
  screening: "info",
  interviewing: "info",
  offer: "warning",
  hired: "success",
  rejected: "danger",
  withdrawn: "neutral",
};

export const PRESCREEN_OUTCOME_LABEL: Record<PrescreenOutcome, string> = {
  advance: "Advance",
  reject: "Reject",
  hold: "Hold",
};

export const PRESCREEN_OUTCOME_VARIANT: Record<PrescreenOutcome, Variant> = {
  advance: "success",
  reject: "danger",
  hold: "warning",
};

export const CANDIDATE_SOURCE_LABEL: Record<CandidateSource, string> = {
  referral: "Referral",
  job_board: "Job board",
  agency: "Agency",
  direct: "Direct",
  other: "Other",
};

export const NOTICE_PERIOD_LABEL: Record<NoticePeriod, string> = {
  immediate: "Immediate",
  one_week: "1 week",
  two_weeks: "2 weeks",
  one_month: "1 month",
  two_months: "2 months",
  three_plus_months: "3+ months",
};

export const FIT_RATING_VARIANT: Record<FitRating, Variant> = {
  "Strong Fit": "success",
  "Good Fit": "info",
  "Possible Fit": "warning",
  "Weak Fit": "danger",
};

// Mirrors FIT_RATING_VARIANT's exact tier-to-variant mapping — the Shadow side's own qualitative
// match tier, kept as a parallel enum rather than reusing FitRating since the two are computed by
// different modules for different audiences (recruiter fit assessment vs. candidate job match).
export const MATCH_TIER_VARIANT: Record<MatchTier, Variant> = {
  "Excellent Match": "success",
  "Strong Match": "info",
  "Potential Match": "warning",
  "Weak Match": "danger",
};

export const SHADOW_JOB_STATUS_LABEL: Record<ShadowJobStatus, string> = {
  draft: "Draft",
  published: "Published",
  closed: "Closed",
};

export const SHADOW_JOB_STATUS_VARIANT: Record<ShadowJobStatus, Variant> = {
  draft: "neutral",
  published: "success",
  closed: "outline",
};

export const SHADOW_APPLICATION_STATUS_LABEL: Record<ShadowApplicationStatus, string> = {
  submitted: "Submitted",
  under_review: "Under review",
  reveal_requested: "Reveal requested",
  revealed: "Revealed",
  declined: "Declined",
  withdrawn: "Withdrawn",
};

export const SHADOW_APPLICATION_STATUS_VARIANT: Record<ShadowApplicationStatus, Variant> = {
  submitted: "info",
  under_review: "neutral",
  reveal_requested: "warning",
  revealed: "success",
  declined: "outline",
  withdrawn: "outline",
};

export const INTERVIEW_STATUS_LABEL: Record<InterviewStatus, string> = {
  scheduled: "Scheduled",
  cancelled: "Cancelled",
  completed: "Completed",
};

export const INTERVIEW_STATUS_VARIANT: Record<InterviewStatus, Variant> = {
  scheduled: "info",
  cancelled: "outline",
  completed: "success",
};

export const REMOTE_PREFERENCE_LABEL: Record<RemotePreference, string> = {
  remote: "Remote",
  hybrid: "Hybrid",
  onsite: "Onsite",
  flexible: "Flexible",
};

export const CAREER_INTENT_LABEL: Record<CareerIntent, string> = {
  actively_looking: "Actively looking",
  open_to_opportunity: "Open to opportunities",
  just_exploring: "Just exploring",
  not_looking: "Not looking",
};

export const EMPLOYMENT_TYPE_LABEL: Record<EmploymentType, string> = {
  full_time: "Full-time",
  part_time: "Part-time",
  contract: "Contract",
  fractional: "Fractional",
};

export const VERIFICATION_STATUS_LABEL: Record<VerificationStatus, string> = {
  unverified: "Not verified",
  pending: "Verification pending",
  verified: "Verified",
};

export const VISIBILITY_LABEL: Record<PassportVisibility, string> = {
  private: "Private",
  match_only: "Match-only",
  discoverable: "Discoverable",
};

// One honest line per state for dynamic helper copy under the visibility toggle -- match_only
// and discoverable read identically today since both are only found via job-anchored AI-matched
// search; discoverable's copy says so rather than promising a general-browse feature that isn't
// built yet, mirroring the Talent Memory beat's own honest-Preview framing.
export const VISIBILITY_DESCRIPTION: Record<PassportVisibility, string> = {
  private: "Companies never see your Passport unless you apply directly.",
  match_only:
    "Companies can find you through AI-matched search for roles you're a strong fit for — even before you apply.",
  discoverable:
    "Same as Match-only today. You'll also appear in general candidate search once that's built.",
};

export const COMPANY_SIZE_LABEL: Record<CompanySizeBand, string> = {
  "1-10": "1–10 employees",
  "11-50": "11–50 employees",
  "51-200": "51–200 employees",
  "201-500": "201–500 employees",
  "500+": "500+ employees",
};

export const SHADOW_FIELD_LABEL: Record<ShadowField, string> = {
  full_name: "Name",
  email: "Email",
  phone: "Phone",
  career_history: "Career history",
};

export const VERIFICATION_STATUS_VARIANT: Record<VerificationStatus, Variant> = {
  unverified: "neutral",
  pending: "info",
  verified: "gold",
};
