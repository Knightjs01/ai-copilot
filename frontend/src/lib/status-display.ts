import type { BadgeProps } from "@/components/ui/badge";
import type {
  CandidateSource,
  CandidateStatus,
  FitRating,
  NoticePeriod,
  PrescreenOutcome,
  ProjectStatus,
} from "@/lib/types";

type Variant = NonNullable<BadgeProps["variant"]>;

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
