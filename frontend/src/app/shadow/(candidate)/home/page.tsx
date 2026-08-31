"use client";

import * as React from "react";
import Link from "next/link";
import {
  Award,
  Bookmark,
  Briefcase,
  Building2,
  ChevronRight,
  FileText,
  IdCard,
  Lock,
  Shield,
  Sparkles,
  UserCog,
  type LucideIcon,
} from "lucide-react";

import { CompanyBoardCard } from "@/components/shadow/company-board-card";
import { EmptyState } from "@/components/shadow/empty-state";
import { ShadowJobCard } from "@/components/shadow/shadow-job-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PassportProgressRing } from "@/components/candidate/passport-wizard/passport-progress-ring";
import { Spinner } from "@/components/ui/spinner";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { companyAvatar } from "@/lib/company-avatar";
import { useCompanyBoard } from "@/lib/queries/company";
import { useBatchJobMatches } from "@/lib/queries/passport-matching";
import { useSavedJobs } from "@/lib/queries/saved-jobs";
import { useMyApplications, useShadowBoard } from "@/lib/queries/shadow-jobs";
import { useMyPassport } from "@/lib/queries/phantom-passport";
import { MATCH_TIER_VARIANT } from "@/lib/status-display";
import type { PhantomPassport, ShadowJobBoardListing } from "@/lib/types";

const NEW_JOB_WINDOW_DAYS = 7;

function isRecentlyPublished(publishedAt: string | null): boolean {
  if (!publishedAt) return false;
  const days = (Date.now() - new Date(publishedAt).getTime()) / (1000 * 60 * 60 * 24);
  return days <= NEW_JOB_WINDOW_DAYS;
}

const TERMINAL_STATUSES = new Set(["declined", "withdrawn"]);
const HOME_MATCH_PREVIEW = 24;
const TOP_MATCHES_SHOWN = 3;
const SAVED_JOBS_SHOWN = 3;
const MIN_SKILLS_TARGET = 3;

// Static product-principle cards -- real, already-established claims restated for this page
// (see passport-showcase-section.tsx's KEY_POINTS and the Discover board's own anonymity copy),
// not new marketing invented for this section.
const VALUE_PROPS = [
  {
    icon: Shield,
    title: "100% private",
    body: "Your identity stays sealed until you personally approve a Reveal Request.",
  },
  {
    icon: Sparkles,
    title: "Matched by real fit",
    body: "Every opportunity here is ranked by your actual skills and experience.",
  },
  {
    icon: UserCog,
    title: "You're in control",
    body: "Choose exactly what's visible, and reveal your identity only when you're ready.",
  },
];

interface SuggestedStep {
  label: string;
  description: string;
  icon: LucideIcon;
}

// Every suggestion is derived from a real Passport field the backend already tracks as part of
// completion_percentage (see phantom_passport/service.py's _completion_percentage) -- never a
// fabricated checklist. "Verify your education" isn't included here because there's no education
// field anywhere on the Passport today.
function deriveSuggestedSteps(passport: PhantomPassport | null | undefined): SuggestedStep[] {
  if (!passport) return [];
  const steps: SuggestedStep[] = [];
  if (passport.career_entries.length === 0) {
    steps.push({
      label: "Add work experience",
      description: "Show your career history.",
      icon: Briefcase,
    });
  }
  if (passport.skills.length < MIN_SKILLS_TARGET) {
    steps.push({ label: "Add key skills", description: "Highlight your expertise.", icon: Sparkles });
  }
  if (!passport.career_entries.some((entry) => entry.achievements.length > 0)) {
    steps.push({ label: "Add achievements", description: "Showcase your impact.", icon: Award });
  }
  if (!passport.summary) {
    steps.push({
      label: "Write a summary",
      description: "Give recruiters a quick overview.",
      icon: FileText,
    });
  }
  return steps;
}

// Built from data that's real today -- Passport completion, active application count, saved job
// count, real AI matches, and real live company profiles. See passport_matching for the matching
// engine the "top matches" section is built on, and companies/service.py's list_board for the
// "Explore companies" data source.
export default function ShadowHomePage() {
  const { candidate } = useCandidateAuth();
  const { data: passport, isLoading: isLoadingPassport } = useMyPassport();
  const { data: applications, isLoading: isLoadingApplications } = useMyApplications();
  const { data: savedJobs, isLoading: isLoadingSaved } = useSavedJobs();
  const { data: companies } = useCompanyBoard(4);

  const isLoading = isLoadingPassport || isLoadingApplications || isLoadingSaved;

  const activeApplicationsCount =
    applications?.filter((application) => !TERMINAL_STATUSES.has(application.status)).length ?? 0;
  const completionPercentage = passport?.completion_percentage ?? 0;
  const passportApproved = passport?.current_version_number != null;
  const suggestedSteps = React.useMemo(() => deriveSuggestedSteps(passport), [passport]);

  const { data: boardJobs } = useShadowBoard();
  const previewJobIds = (boardJobs ?? []).slice(0, HOME_MATCH_PREVIEW).map((job) => job.id);
  const { data: matches } = useBatchJobMatches(previewJobIds, { enabled: passportApproved });
  const topMatches = React.useMemo(() => {
    if (!boardJobs || !matches) return [];
    const jobById = new Map(boardJobs.map((job) => [job.id, job]));
    const entries: { match: (typeof matches)[number]; job: ShadowJobBoardListing }[] = [];
    for (const match of matches) {
      const job = jobById.get(match.job_id);
      if (job) entries.push({ match, job });
    }
    return entries.sort((a, b) => b.match.match_score - a.match.match_score).slice(0, TOP_MATCHES_SHOWN);
  }, [boardJobs, matches]);

  const subheading = !passport
    ? "Build your Phantom Passport to start discovering opportunities."
    : !passportApproved
      ? "Finish and approve your Passport to start applying."
      : activeApplicationsCount > 0
        ? `You have ${activeApplicationsCount} active application${activeApplicationsCount === 1 ? "" : "s"}.`
        : "Browse Discover to find your next opportunity.";

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px] lg:items-start">
      <div className="flex flex-col gap-8">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            {candidate ? `Good to see you, ${candidate.first_name}.` : "Welcome back."}
          </h1>
          <p className="text-sm text-muted-foreground">{subheading}</p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Link href="/shadow/passport">
            <Card className="h-full transition-colors hover:border-brand/40">
              <CardContent className="flex flex-col gap-2 py-6">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <IdCard className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wide">Passport</span>
                </div>
                <span className="text-2xl font-semibold text-foreground">
                  {completionPercentage}%
                </span>
                <span className="text-xs text-muted-foreground">
                  {passportApproved ? "Approved" : "Complete"}
                </span>
              </CardContent>
            </Card>
          </Link>

          <Link href="/shadow/applications">
            <Card className="h-full transition-colors hover:border-brand/40">
              <CardContent className="flex flex-col gap-2 py-6">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Briefcase className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wide">
                    Active applications
                  </span>
                </div>
                <span className="text-2xl font-semibold text-foreground">
                  {activeApplicationsCount}
                </span>
                <span className="text-xs text-muted-foreground">In progress</span>
              </CardContent>
            </Card>
          </Link>

          <Link href="/shadow/saved-jobs">
            <Card className="h-full transition-colors hover:border-brand/40">
              <CardContent className="flex flex-col gap-2 py-6">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Bookmark className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wide">Saved jobs</span>
                </div>
                <span className="text-2xl font-semibold text-foreground">
                  {savedJobs?.length ?? 0}
                </span>
                <span className="text-xs text-muted-foreground">
                  {(savedJobs?.length ?? 0) === 1 ? "Role saved" : "Roles saved"}
                </span>
              </CardContent>
            </Card>
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {VALUE_PROPS.map((prop) => (
            <div key={prop.title} className="flex flex-col gap-2.5 rounded-2xl border border-border bg-card p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand/10 text-brand">
                <prop.icon className="h-4.5 w-4.5" />
              </div>
              <p className="text-sm font-semibold text-foreground">{prop.title}</p>
              <p className="text-xs leading-relaxed text-muted-foreground">{prop.body}</p>
            </div>
          ))}
        </div>

        {passportApproved && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-brand" />
                <h2 className="text-base font-semibold text-foreground">Recommended for you</h2>
              </div>
              {topMatches.length > 0 && (
                <Link href="/shadow/for-you" className="text-xs font-medium text-brand hover:underline">
                  View all matches
                </Link>
              )}
            </div>
            {topMatches.length > 0 ? (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {topMatches.map(({ job, match }) => (
                  <ShadowJobCard
                    key={job.id}
                    job={job}
                    match={match}
                    description={match.summary}
                    showSeniority={false}
                    showRequirements={false}
                    showCompanyLink={false}
                    showCompanyAvatar
                    isNew={isRecentlyPublished(job.published_at)}
                  />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={Sparkles}
                title="No matches yet"
                description="Check back once more roles are posted."
                action={{ label: "Browse Discover", href: "/shadow" }}
              />
            )}
          </div>
        )}

        {!passportApproved && (
          <Card>
            <CardContent className="flex flex-col items-start gap-3 py-6 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-col gap-0.5">
                <h2 className="text-sm font-semibold text-foreground">
                  {passport ? "Your Passport isn't approved yet" : "You haven't built a Passport yet"}
                </h2>
                <p className="text-sm text-muted-foreground">
                  Nothing becomes visible to a company until you review and approve it.
                </p>
              </div>
              <Button asChild variant="brand">
                <Link href="/shadow/passport">
                  {passport ? "Finish your Passport" : "Build your Passport"}
                </Link>
              </Button>
            </CardContent>
          </Card>
        )}

        {passportApproved && activeApplicationsCount === 0 && (
          <Card>
            <CardContent className="flex flex-col items-start gap-3 py-6 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-col gap-0.5">
                <h2 className="text-sm font-semibold text-foreground">Nothing applied to yet</h2>
                <p className="text-sm text-muted-foreground">
                  Browse open roles and apply in seconds with your Passport.
                </p>
              </div>
              <Button asChild variant="brand">
                <Link href="/shadow">Discover roles</Link>
              </Button>
            </CardContent>
          </Card>
        )}

        {companies && companies.length > 0 && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-brand" />
                <h2 className="text-base font-semibold text-foreground">Explore companies</h2>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {companies.map((company) => (
                <CompanyBoardCard key={company.slug} company={company} />
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-5">
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-6 text-center">
            <PassportProgressRing percentage={completionPercentage} />
            <p className="text-sm font-semibold text-foreground">
              {completionPercentage >= 80 ? "Strong" : completionPercentage >= 40 ? "Building" : "Just started"}
            </p>
            <p className="text-xs text-muted-foreground">
              {passportApproved
                ? "Your Passport is approved and visible to matching roles."
                : "Complete a few more steps to improve your matches."}
            </p>
            <Button asChild variant="secondary" size="sm" className="w-full">
              <Link href="/shadow/passport">Continue improving</Link>
            </Button>
          </CardContent>
        </Card>

        {suggestedSteps.length > 0 && (
          <Card>
            <CardContent className="flex flex-col gap-1 py-5">
              <p className="mb-2 text-sm font-semibold text-foreground">Suggested next steps</p>
              {suggestedSteps.map((step) => (
                <Link
                  key={step.label}
                  href="/shadow/passport"
                  className="flex items-center gap-3 rounded-lg px-1 py-2 transition-colors hover:bg-secondary/50"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand/10 text-brand">
                    <step.icon className="h-4 w-4" />
                  </div>
                  <div className="flex flex-1 flex-col">
                    <span className="text-sm font-medium text-foreground">{step.label}</span>
                    <span className="text-xs text-muted-foreground">{step.description}</span>
                  </div>
                  <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                </Link>
              ))}
            </CardContent>
          </Card>
        )}

        {savedJobs && savedJobs.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center gap-2 py-5 text-center">
              <Bookmark className="h-4 w-4 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                No saved roles yet.{" "}
                <Link href="/shadow" className="font-medium text-brand hover:underline">
                  Browse Discover
                </Link>
                .
              </p>
            </CardContent>
          </Card>
        )}

        {savedJobs && savedJobs.length > 0 && (
          <Card>
            <CardContent className="flex flex-col gap-3 py-5">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-foreground">Saved opportunities</p>
                <Link href="/shadow/saved-jobs" className="text-xs font-medium text-brand hover:underline">
                  View all
                </Link>
              </div>
              <div className="flex flex-col gap-2.5">
                {savedJobs.slice(0, SAVED_JOBS_SHOWN).map((saved) => {
                  const avatar = companyAvatar(saved.job.company_name);
                  return (
                    <Link
                      key={saved.id}
                      href={`/shadow/jobs/${saved.job.id}`}
                      className="flex items-center justify-between gap-2 text-sm"
                    >
                      <div className="flex items-center gap-2.5">
                        <div
                          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-semibold ${avatar.colorClassName}`}
                        >
                          {avatar.initial}
                        </div>
                        <div className="flex flex-col">
                          <span className="font-medium text-foreground">{saved.job.title}</span>
                          <span className="text-xs text-muted-foreground">
                            {saved.job.company_name}
                          </span>
                        </div>
                      </div>
                      <Bookmark className="h-3.5 w-3.5 shrink-0 fill-brand text-brand" />
                    </Link>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardContent className="flex flex-col gap-2 py-5">
            <div className="flex items-center gap-2">
              <Lock className="h-4 w-4 text-brand" />
              <p className="text-sm font-semibold text-foreground">Privacy is built in</p>
            </div>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Your activity is private and never shared with a company until you choose to apply.
            </p>
            <Badge variant="neutral" className="w-fit">
              Callsign: {passport?.callsign ?? "Not yet assigned"}
            </Badge>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
