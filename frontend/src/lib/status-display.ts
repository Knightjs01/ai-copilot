import type { BadgeProps } from "@/components/ui/badge";
import type {
  CandidateSource,
  CandidateStatus,
  CareerIntent,
  EmploymentType,
  FitRating,
  NoticePeriod,
  PrescreenOutcome,
  ProjectStatus,
  RemotePreference,
  RoleName,
  ShadowApplicationStatus,
  ShadowJobStatus,
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
