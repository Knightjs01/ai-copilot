"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Eye, Lock, MessageCircle, ShieldAlert, Sparkles } from "lucide-react";

import { ActivityTab } from "@/components/shadow-jobs/candidate-workspace/activity-tab";
import { ApplicationTab } from "@/components/shadow-jobs/candidate-workspace/application-tab";
import { ExperienceTab } from "@/components/shadow-jobs/candidate-workspace/experience-tab";
import { InterviewsTab } from "@/components/shadow-jobs/candidate-workspace/interviews-tab";
import { MatchTab } from "@/components/shadow-jobs/candidate-workspace/match-tab";
import { NotesSection } from "@/components/shadow-jobs/candidate-workspace/notes-section";
import { RequestRevealDialog } from "@/components/shadow-jobs/request-reveal-dialog";
import { SaveToTalentPoolDialog } from "@/components/shadow-jobs/save-to-talent-pool-dialog";
import { ScheduleInterviewDialog } from "@/components/shadow-jobs/schedule-interview-dialog";
import { StepUpDialog } from "@/components/step-up-dialog";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { Tabs } from "@/components/ui/tabs";
import { useAuth } from "@/lib/auth-context";
import { useApplicantMatch } from "@/lib/queries/candidate-search";
import {
  useApplicant,
  useMarkApplicantViewed,
  useMyShadowJob,
  useUpdateApplicantPipelineStage,
} from "@/lib/queries/shadow-jobs";
import { useFetchRevealedIdentity } from "@/lib/queries/shadow-reveal";
import {
  CAREER_INTENT_LABEL,
  MATCH_TIER_VARIANT,
  NOTICE_PERIOD_LABEL,
  REMOTE_PREFERENCE_LABEL,
  SHADOW_APPLICATION_STATUS_LABEL,
  SHADOW_APPLICATION_STATUS_VARIANT,
  SHADOW_EFFECTIVE_STAGE_LABEL,
  SHADOW_EFFECTIVE_STAGE_VARIANT,
  TALENT_POOL_STATUS_LABEL,
  TALENT_POOL_STATUS_VARIANT,
} from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { useToast } from "@/lib/toast-context";
import type { RevealedIdentity, ShadowPipelineStage, ShadowProfile } from "@/lib/types";

const WORKSPACE_TABS = [
  "overview",
  "match",
  "experience",
  "application",
  "interviews",
  "activity",
] as const;
type WorkspaceTab = (typeof WORKSPACE_TABS)[number];

const SHADOW_ASSIGNABLE_STAGES: ShadowPipelineStage[] = [
  "new",
  "screening",
  "interviewing",
  "offer",
  "hired",
  "rejected",
];

function formatSalary(min: number | null, max: number | null): string | null {
  if (min == null && max == null) return null;
  const fmt = (n: number) => `£${(n / 1000).toFixed(0)}k`;
  if (min != null && max != null) return `${fmt(min)}–${fmt(max)}`;
  return fmt((min ?? max) as number);
}

export default function CandidateWorkspacePage() {
  const params = useParams<{ jobId: string; applicationId: string }>();
  const { hasPermission } = useAuth();
  const toast = useToast();
  const container = useThemeScopeContainer();
  const canView = hasPermission("shadow_jobs.view");
  const [activeTab, setActiveTab] = React.useState<WorkspaceTab>("overview");

  const { data: job } = useMyShadowJob(params.jobId);
  const { data: profile, isLoading } = useApplicant(params.jobId, params.applicationId);
  const { data: match } = useApplicantMatch(params.jobId, params.applicationId);
  const updateStage = useUpdateApplicantPipelineStage(params.jobId);
  const markViewed = useMarkApplicantViewed(params.jobId);
  const markViewedRef = React.useRef(markViewed.mutate);
  markViewedRef.current = markViewed.mutate;

  const [identity, setIdentity] = React.useState<RevealedIdentity | null>(null);
  const [stepUpOpen, setStepUpOpen] = React.useState(false);
  const fetchIdentity = useFetchRevealedIdentity(params.jobId);

  // Opening this page is a real "the recruiter looked at this applicant" signal, same trigger
  // the card list already uses -- clears both the new-application and unseen-reveal-response
  // flags the moment the workspace is actually viewed.
  React.useEffect(() => {
    if (profile && (profile.is_new || profile.reveal_response_is_new)) {
      markViewedRef.current(profile.application_id);
    }
  }, [profile?.is_new, profile?.reveal_response_is_new, profile?.application_id]);

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">
          This candidate workspace isn&apos;t available on your role
        </p>
      </div>
    );
  }

  if (isLoading || !profile) {
    return (
      <div className="flex justify-center py-24">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  const isRevealable = profile.status === "revealed";
  const canRequestTalentPool =
    hasPermission("talent_pool.request") &&
    (job?.status === "closed" || profile.status === "declined" || profile.status === "withdrawn");
  const talentPoolActionable =
    canRequestTalentPool &&
    (profile.talent_pool_status === null ||
      profile.talent_pool_status === "declined" ||
      profile.talent_pool_status === "withdrawn");

  const handleVerified = async (stepUpToken: string) => {
    const result = await fetchIdentity.mutateAsync({
      applicationId: profile.application_id,
      stepUpToken,
    });
    setIdentity(result);
  };

  const handleStageChange = (value: ShadowPipelineStage) => {
    updateStage.mutate(
      { applicationId: profile.application_id, pipelineStage: value },
      { onError: () => toast({ title: "Couldn't update stage", variant: "danger" }) }
    );
  };

  const factsLine = [
    profile.industries.join(", ") || null,
    profile.location,
    profile.remote_preference ? REMOTE_PREFERENCE_LABEL[profile.remote_preference] : null,
    formatSalary(profile.salary_min, profile.salary_max),
    profile.notice_period ? `${NOTICE_PERIOD_LABEL[profile.notice_period]} notice` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  const nextStep = deriveNextStep(profile);

  const tabOptions: { value: WorkspaceTab; label: string }[] = [
    { value: "overview", label: "Overview" },
    { value: "match", label: "Match" },
    { value: "experience", label: "Experience" },
    { value: "application", label: "Application" },
    { value: "interviews", label: "Interviews" },
    { value: "activity", label: "Activity" },
  ];

  return (
    <div className="flex flex-col gap-6">
      <Link
        href={`/shadow-jobs/${params.jobId}`}
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to applicants
      </Link>

      {/* --- Header ------------------------------------------------------------------------- */}
      <Card>
        <CardContent className="flex flex-col gap-4 py-5">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
            <div className="flex items-start gap-3">
              <Avatar name={profile.callsign} className="h-11 w-11 text-sm" />
              <div className="flex flex-col gap-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-xl font-semibold tracking-tight text-foreground">
                    {profile.callsign}
                  </h1>
                  {match && (
                    <Badge variant={MATCH_TIER_VARIANT[match.match_tier]}>
                      {match.match_score}% Match
                    </Badge>
                  )}
                  <Badge variant={SHADOW_EFFECTIVE_STAGE_VARIANT[profile.effective_stage]}>
                    {SHADOW_EFFECTIVE_STAGE_LABEL[profile.effective_stage]}
                  </Badge>
                  <span className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
                    {isRevealable ? (
                      <>
                        <Eye className="h-3 w-3" /> Revealed
                      </>
                    ) : (
                      <>
                        <Lock className="h-3 w-3" /> Anonymous
                      </>
                    )}
                  </span>
                </div>
                {profile.headline && (
                  <p className="text-sm font-medium text-foreground">{profile.headline}</p>
                )}
                {factsLine && <p className="text-sm text-muted-foreground">{factsLine}</p>}
              </div>
            </div>

            <div className="flex shrink-0 flex-wrap items-center gap-2">
              {isRevealable ? (
                identity ? (
                  <Badge variant="success">Identity revealed</Badge>
                ) : (
                  <Button
                    type="button"
                    variant="brand"
                    size="sm"
                    onClick={() => setStepUpOpen(true)}
                    disabled={fetchIdentity.isPending}
                  >
                    <Eye className="h-3.5 w-3.5" />
                    {fetchIdentity.isPending ? "Verifying…" : "Reveal Identity"}
                  </Button>
                )
              ) : profile.status === "submitted" || profile.status === "under_review" ? (
                <RequestRevealDialog
                  jobId={params.jobId}
                  applicationId={profile.application_id}
                  callsign={profile.callsign}
                />
              ) : null}
              {hasPermission("interviews.view") && (
                <ScheduleInterviewDialog
                  jobId={params.jobId}
                  applicationId={profile.application_id}
                  callsign={profile.callsign}
                />
              )}
              {hasPermission("messages.view") && (
                <Button variant="secondary" size="sm" asChild>
                  <Link href={`/shadow-jobs/${params.jobId}/applicants/${profile.application_id}/messages`}>
                    <MessageCircle className="h-3.5 w-3.5" />
                    Message
                    {profile.unread_message_count > 0 && (
                      <Badge variant="info" className="ml-1">
                        {profile.unread_message_count}
                      </Badge>
                    )}
                  </Link>
                </Button>
              )}
            </div>
          </div>

          {identity && (
            <div className="flex flex-col gap-1 rounded-xl border border-success/30 bg-success/5 p-3">
              <div className="flex items-center gap-1.5 text-sm font-medium text-success">
                <Eye className="h-3.5 w-3.5" />
                Identity revealed
              </div>
              {identity.full_name && <p className="text-sm text-foreground">{identity.full_name}</p>}
              {identity.email && <p className="text-sm text-muted-foreground">{identity.email}</p>}
              {identity.phone && <p className="text-sm text-muted-foreground">{identity.phone}</p>}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3 border-t border-border pt-3">
            <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Role stage
            </span>
            <Select
              value={profile.pipeline_stage}
              onValueChange={(value) => handleStageChange(value as ShadowPipelineStage)}
              disabled={profile.effective_stage === "withdrawn"}
            >
              <SelectTrigger className="h-8 w-40 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent container={container}>
                {SHADOW_ASSIGNABLE_STAGES.map((stage) => (
                  <SelectItem key={stage} value={stage}>
                    {SHADOW_EFFECTIVE_STAGE_LABEL[stage]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {profile.effective_stage !== "withdrawn" && (
              <Badge variant={SHADOW_APPLICATION_STATUS_VARIANT[profile.status]}>
                {SHADOW_APPLICATION_STATUS_LABEL[profile.status]}
              </Badge>
            )}

            {canRequestTalentPool && (
              <div className="ml-auto flex items-center gap-2">
                {talentPoolActionable ? (
                  <SaveToTalentPoolDialog
                    jobId={params.jobId}
                    applicationId={profile.application_id}
                    callsign={profile.callsign}
                  />
                ) : profile.talent_pool_status === "granted" ? (
                  <Badge variant={TALENT_POOL_STATUS_VARIANT.granted}>
                    {TALENT_POOL_STATUS_LABEL.granted}
                  </Badge>
                ) : profile.talent_pool_status === "requested" ? (
                  <span className="text-xs text-muted-foreground">Talent Pool request pending</span>
                ) : null}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* --- Body: main content + Passport sidebar ------------------------------------------ */}
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="order-2 flex min-w-0 flex-col gap-5 lg:order-1">
          <Tabs options={tabOptions} value={activeTab} onChange={setActiveTab} />

          {activeTab === "overview" && (
            <OverviewTab
              jobId={params.jobId}
              jobTitle={job?.title ?? ""}
              profile={profile}
              nextStep={nextStep}
              onOpenTab={setActiveTab}
            />
          )}
          {activeTab === "match" && (
            <MatchTab jobId={params.jobId} applicationId={profile.application_id} />
          )}
          {activeTab === "experience" && <ExperienceTab profile={profile} />}
          {activeTab === "application" && (
            <ApplicationTab jobTitle={job?.title ?? ""} profile={profile} />
          )}
          {activeTab === "interviews" && (
            <InterviewsTab jobId={params.jobId} applicationId={profile.application_id} />
          )}
          {activeTab === "activity" && (
            <ActivityTab jobId={params.jobId} applicationId={profile.application_id} />
          )}
        </div>

        {/* --- Candidate Passport ----------------------------------------------------------- */}
        <div className="order-1 flex flex-col gap-4 lg:sticky lg:top-6 lg:order-2 lg:self-start">
          <Card>
            <CardContent className="flex flex-col gap-3 py-5">
              <div className="flex items-center gap-1.5">
                <Sparkles className="h-4 w-4 text-brand" />
                <h2 className="text-sm font-semibold text-foreground">Candidate Passport</h2>
              </div>
              <p className="text-lg font-semibold tracking-tight text-foreground">
                {profile.callsign}
              </p>
              <div className="flex flex-col gap-2 text-sm">
                {profile.years_experience != null && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Experience</span>
                    <span className="text-foreground">{profile.years_experience} years</span>
                  </div>
                )}
                {profile.location && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Location</span>
                    <span className="text-foreground">{profile.location}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Career intent</span>
                  <span className="text-foreground">{CAREER_INTENT_LABEL[profile.career_intent]}</span>
                </div>
                {profile.notice_period && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Availability</span>
                    <span className="text-foreground">
                      {NOTICE_PERIOD_LABEL[profile.notice_period]} notice
                    </span>
                  </div>
                )}
              </div>
              <Button
                variant="secondary"
                size="sm"
                className="mt-1"
                onClick={() => setActiveTab("experience")}
              >
                View full experience
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      <StepUpDialog
        open={stepUpOpen}
        onOpenChange={setStepUpOpen}
        title="Confirm it's you"
        description="Viewing a revealed identity is a high-risk action — re-enter your password to continue."
        onVerified={handleVerified}
      />
    </div>
  );
}

interface NextStep {
  message: string;
  cta: "reveal" | "interview" | null;
}

function deriveNextStep(profile: {
  effective_stage: string;
  status: string;
  has_upcoming_interview: boolean;
}): NextStep {
  if (profile.effective_stage === "withdrawn") {
    return { message: "This candidate withdrew their application.", cta: null };
  }
  if (profile.effective_stage === "rejected") {
    return { message: "This applicant is marked rejected.", cta: null };
  }
  if (profile.effective_stage === "hired") {
    return { message: "This applicant is marked hired.", cta: null };
  }
  if (profile.status === "revealed") {
    return profile.has_upcoming_interview
      ? { message: "Identity revealed and an interview is already scheduled.", cta: null }
      : { message: "Identity revealed — arrange an interview.", cta: "interview" };
  }
  if (profile.status === "reveal_requested") {
    return { message: "Waiting on the candidate to respond to your reveal request.", cta: null };
  }
  if (profile.status === "declined") {
    return { message: "This candidate declined your reveal request.", cta: null };
  }
  return {
    message: "Review this application and request a reveal when you're ready to move forward.",
    cta: "reveal",
  };
}

function OverviewTab({
  jobId,
  jobTitle,
  profile,
  nextStep,
  onOpenTab,
}: {
  jobId: string;
  jobTitle: string;
  profile: ShadowProfile;
  nextStep: NextStep;
  onOpenTab: (tab: WorkspaceTab) => void;
}) {
  const { data: match, isLoading: matchLoading, isError: matchErrored } = useApplicantMatch(
    jobId,
    profile.application_id
  );

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardContent className="flex flex-col gap-3 py-5">
          <h2 className="text-sm font-semibold text-foreground">Why this candidate?</h2>
          {match && match.strengths.length > 0 ? (
            <ol className="flex flex-col gap-2.5">
              {match.strengths.map((strength, i) => (
                <li key={i} className="flex gap-2.5 text-sm text-foreground">
                  <span className="shrink-0 font-mono text-xs text-muted-foreground">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  {strength}
                </li>
              ))}
            </ol>
          ) : matchErrored ? (
            <p className="text-sm text-muted-foreground">Couldn&apos;t compute a match summary.</p>
          ) : matchLoading ? (
            <p className="text-sm text-muted-foreground">Computing a match summary…</p>
          ) : (
            <p className="text-sm text-muted-foreground">No match evidence available.</p>
          )}
          {match && match.gaps.length > 0 && (
            <div className="mt-1 border-t border-border pt-3">
              <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Potential considerations
              </p>
              <ul className="flex flex-col gap-1">
                {match.gaps.map((gap, i) => (
                  <li key={i} className="text-sm text-foreground">
                    • {gap}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        <button type="button" onClick={() => onOpenTab("match")} className="text-left">
          <Card className="h-full transition-colors hover:border-brand/40">
            <CardContent className="flex flex-col gap-1.5 py-4">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Phantom Match
              </p>
              {match ? (
                <>
                  <p className="text-2xl font-semibold text-foreground">{match.match_score}%</p>
                  <Badge variant={MATCH_TIER_VARIANT[match.match_tier]} className="w-fit">
                    {match.match_tier}
                  </Badge>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">View match details →</p>
              )}
            </CardContent>
          </Card>
        </button>

        <button type="button" onClick={() => onOpenTab("application")} className="text-left">
          <Card className="h-full transition-colors hover:border-brand/40">
            <CardContent className="flex flex-col gap-1.5 py-4">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Application
              </p>
              <p className="text-sm font-medium text-foreground">{jobTitle}</p>
              <p className="text-xs text-muted-foreground">
                {SHADOW_APPLICATION_STATUS_LABEL[profile.status]}
              </p>
            </CardContent>
          </Card>
        </button>
      </div>

      <Card>
        <CardContent className="flex flex-col gap-3 py-5">
          <h2 className="text-sm font-semibold text-foreground">Next step</h2>
          <p className="text-sm text-foreground">{nextStep.message}</p>
          {nextStep.cta === "interview" && (
            <div>
              <ScheduleInterviewDialog
                jobId={jobId}
                applicationId={profile.application_id}
                callsign={profile.callsign}
              />
            </div>
          )}
          {nextStep.cta === "reveal" && (
            <div>
              <RequestRevealDialog
                jobId={jobId}
                applicationId={profile.application_id}
                callsign={profile.callsign}
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="py-5">
          <NotesSection jobId={jobId} applicationId={profile.application_id} />
        </CardContent>
      </Card>
    </div>
  );
}
