"use client";

import * as React from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, BadgeCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { StatTile } from "@/components/ui/stat-tile";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { JobRow } from "@/components/platform-admin/job-row";
import { EditCommercialDialog } from "@/components/platform-admin/edit-commercial-dialog";
import { ProfileReviewDialog } from "@/components/platform-admin/profile-review-dialog";
import {
  useAdminJobs,
  useCompanyActivity,
  useCompanyDetail,
  useCompanyUsers,
  useReactivateCompany,
  useSuspendCompany,
  useUnverifyCompany,
  useVerifyCompany,
} from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import { COMPANY_PROFILE_STATUS_LABEL, COMPANY_PROFILE_STATUS_VARIANT } from "@/lib/status-display";
import type { AuditEntry } from "@/lib/types";

type TabKey = "overview" | "profile" | "people" | "jobs" | "activity" | "verification";

const TABS: { value: TabKey; label: string }[] = [
  { value: "overview", label: "Overview" },
  { value: "profile", label: "Profile" },
  { value: "people", label: "People" },
  { value: "jobs", label: "Jobs" },
  { value: "activity", label: "Activity" },
  { value: "verification", label: "Verification" },
];

const ACTIVITY_ACTION_LABEL: Record<string, string> = {
  "company.suspended": "Suspended company",
  "company.reactivated": "Reactivated company",
  "company.verified_employer_set": "Updated verified-employer status",
  "company_profile.approved": "Approved profile",
  "company_profile.rejected": "Rejected profile",
  "company.profile_submitted_for_review": "Submitted profile for review",
  "company.profile_self_published": "Published profile changes",
  "company.profile_paused": "Paused profile",
  "company.profile_resumed": "Resumed profile",
  "shadow_job.created": "Created a Shadow job",
  "shadow_job.submitted_for_review": "Submitted job for review",
  "shadow_job.published": "Published job",
  "shadow_job.rejected": "Rejected job",
  "shadow_job.closed": "Closed job",
};

function ActivityRow({ entry }: { entry: AuditEntry }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-1 py-4">
        <div className="flex items-center gap-2">
          <Badge variant="outline">{ACTIVITY_ACTION_LABEL[entry.action] ?? entry.action}</Badge>
          {entry.actor_email && (
            <p className="text-sm text-muted-foreground">{entry.actor_email}</p>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          {new Date(entry.created_at).toLocaleString()}
        </p>
      </CardContent>
    </Card>
  );
}

export default function PlatformAdminCompanyDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();
  const [activeTab, setActiveTab] = React.useState<TabKey>("overview");
  const { data: company, isLoading } = useCompanyDetail(params.id);
  const { data: users, isLoading: usersLoading } = useCompanyUsers(params.id);
  const { data: jobsData, isLoading: jobsLoading } = useAdminJobs(undefined, params.id);
  const jobs = jobsData?.items;
  const { data: activity, isLoading: activityLoading } = useCompanyActivity(params.id);
  const suspend = useSuspendCompany();
  const reactivate = useReactivateCompany();
  const verify = useVerifyCompany();
  const unverify = useUnverifyCompany();
  const isMutating =
    suspend.isPending || reactivate.isPending || verify.isPending || unverify.isPending;

  React.useEffect(() => {
    const tab = searchParams.get("tab");
    if (TABS.some((t) => t.value === tab)) setActiveTab(tab as TabKey);
  }, [searchParams]);

  React.useEffect(() => {
    if (authLoading) return;
    if (!admin) router.push("/platform-admin/login");
    else if (!hasPermission("companies.view")) router.push("/platform-admin");
  }, [authLoading, admin, hasPermission, router]);

  if (authLoading || !admin || !hasPermission("companies.view") || isLoading || !company) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  const adminCount = users?.filter((u) => u.roles.includes("Owner") || u.roles.includes("TA Admin"))
    .length ?? 0;

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <PlatformAdminNav admin={admin} />

      <Link
        href="/platform-admin/companies"
        className="inline-flex w-fit items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Companies
      </Link>

      <div className="flex flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold text-foreground">{company.name}</h1>
          <Badge variant={company.status === "suspended" ? "danger" : "success"}>
            {company.status}
          </Badge>
          <Badge variant={COMPANY_PROFILE_STATUS_VARIANT[company.profile_status]}>
            {COMPANY_PROFILE_STATUS_LABEL[company.profile_status]}
          </Badge>
          {company.is_verified_employer && (
            <Badge variant="gold">
              <BadgeCheck className="h-3 w-3" />
              Verified employer
            </Badge>
          )}
        </div>
        <p className="text-sm text-muted-foreground">
          {company.email_domain} · {company.user_count} member
          {company.user_count === 1 ? "" : "s"} · created{" "}
          {new Date(company.created_at).toLocaleDateString()}
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {TABS.map((tab) => (
          <button
            key={tab.value}
            type="button"
            onClick={() => setActiveTab(tab.value)}
            className={
              tab.value === activeTab
                ? "rounded-full bg-foreground px-3 py-1.5 text-xs font-medium text-background"
                : "rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatTile label="Active roles" value={company.profile_stats.active_role_count} />
            <StatTile label="Total hires" value={company.profile_stats.total_hires} />
            <StatTile
              label="Team size"
              value={company.profile_stats.team_size ?? 0}
            />
            <StatTile
              label="In pipeline"
              value={company.profile_stats.candidates_in_pipeline}
            />
          </div>
          <div className="flex items-center gap-2">
            <EditCommercialDialog company={company} />
            {company.commercial_plan_code && (
              <Badge variant="outline">
                {company.commercial_plan_code.charAt(0).toUpperCase() +
                  company.commercial_plan_code.slice(1)}
                {company.active_role_limit_override !== null &&
                  ` (${company.active_role_limit_override} override)`}
              </Badge>
            )}
          </div>
        </div>
      )}

      {activeTab === "profile" && (
        <div className="flex flex-col gap-4">
          {company.profile_status === "pending_review" && (
            <ProfileReviewDialog companyId={company.id} companyName={company.name} />
          )}
          <Card>
            <CardContent className="flex flex-col gap-3 py-5 text-sm">
              {company.tagline && <p className="font-medium text-foreground">{company.tagline}</p>}
              {company.description && (
                <p className="whitespace-pre-wrap text-muted-foreground">{company.description}</p>
              )}
              <p className="text-muted-foreground">
                {[company.headquarters, company.website, company.founded_year && `Founded ${company.founded_year}`, company.employee_count && `${company.employee_count} employees`]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
              {company.industry.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {company.industry.map((i) => (
                    <Badge key={i} variant="outline">
                      {i}
                    </Badge>
                  ))}
                </div>
              )}
              {company.culture && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Culture
                  </p>
                  <p className="whitespace-pre-wrap text-muted-foreground">{company.culture}</p>
                </div>
              )}
              {company.benefits.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Benefits
                  </p>
                  <ul className="list-inside list-disc text-muted-foreground">
                    {company.benefits.map((b) => (
                      <li key={b}>{b}</li>
                    ))}
                  </ul>
                </div>
              )}
              {company.values.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Values
                  </p>
                  <ul className="list-inside list-disc text-muted-foreground">
                    {company.values.map((v) => (
                      <li key={v.title}>
                        <span className="font-medium text-foreground">{v.title}</span> — {v.body}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {company.hiring_highlights.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Hiring highlights
                  </p>
                  <ul className="list-inside list-disc text-muted-foreground">
                    {company.hiring_highlights.map((h) => (
                      <li key={h.title}>
                        <span className="font-medium text-foreground">{h.title}</span> — {h.body}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === "people" && (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-muted-foreground">
            {adminCount} Owner{adminCount === 1 ? "" : "s"}/TA Admin{adminCount === 1 ? "" : "s"} ·{" "}
            {(users?.length ?? 0) - adminCount} other member
            {(users?.length ?? 0) - adminCount === 1 ? "" : "s"}
          </p>
          {usersLoading && (
            <div className="flex justify-center py-10">
              <Spinner className="h-5 w-5 text-muted-foreground" />
            </div>
          )}
          {!usersLoading &&
            users?.map((user) => (
              <Card key={user.id}>
                <CardContent className="flex flex-col gap-1 py-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex flex-col gap-0.5">
                    <p className="text-sm font-medium text-foreground">{user.full_name}</p>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {user.roles.map((role) => (
                      <Badge key={role} variant="outline">
                        {role}
                      </Badge>
                    ))}
                    {!user.is_active && <Badge variant="danger">Inactive</Badge>}
                  </div>
                </CardContent>
              </Card>
            ))}
        </div>
      )}

      {activeTab === "jobs" && (
        <div className="flex flex-col gap-3">
          {jobsLoading && (
            <div className="flex justify-center py-10">
              <Spinner className="h-5 w-5 text-muted-foreground" />
            </div>
          )}
          {!jobsLoading && jobs?.length === 0 && (
            <p className="py-6 text-center text-sm text-muted-foreground">
              No Shadow jobs for this company yet.
            </p>
          )}
          {!jobsLoading && jobs?.map((job) => <JobRow key={job.id} job={job} />)}
        </div>
      )}

      {activeTab === "activity" && (
        <div className="flex flex-col gap-3">
          {activityLoading && (
            <div className="flex justify-center py-10">
              <Spinner className="h-5 w-5 text-muted-foreground" />
            </div>
          )}
          {!activityLoading && activity?.length === 0 && (
            <p className="py-6 text-center text-sm text-muted-foreground">
              No recorded activity for this company yet.
            </p>
          )}
          {!activityLoading && activity?.map((entry) => <ActivityRow key={entry.id} entry={entry} />)}
        </div>
      )}

      {activeTab === "verification" && (
        <div className="flex flex-col gap-4">
          <Card>
            <CardContent className="flex flex-col gap-3 py-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">Domain verification</p>
                  <p className="text-xs text-muted-foreground">
                    Automatic heuristic (not a free email provider) — not a real ownership check.
                  </p>
                </div>
                <Badge variant={company.is_verified_domain ? "success" : "outline"}>
                  {company.is_verified_domain ? "Verified" : "Unverified"}
                </Badge>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex flex-col gap-3 py-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">Verified employer</p>
                  <p className="text-xs text-muted-foreground">
                    A real, admin-set signal shown to candidates.
                  </p>
                </div>
                {company.is_verified_employer ? (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => unverify.mutate(company.id)}
                    disabled={isMutating}
                  >
                    {unverify.isPending ? "Removing…" : "Unverify"}
                  </Button>
                ) : (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => verify.mutate(company.id)}
                    disabled={isMutating}
                  >
                    {verify.isPending ? "Verifying…" : "Verify employer"}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex flex-col gap-3 py-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">Account status</p>
                  <p className="text-xs text-muted-foreground">
                    Suspending blocks every user at this company from signing in.
                  </p>
                </div>
                {company.status === "suspended" ? (
                  <Button
                    type="button"
                    variant="brand"
                    size="sm"
                    onClick={() => reactivate.mutate(company.id)}
                    disabled={isMutating}
                  >
                    {reactivate.isPending ? "Reactivating…" : "Reactivate"}
                  </Button>
                ) : (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => suspend.mutate(company.id)}
                    disabled={isMutating}
                  >
                    {suspend.isPending ? "Suspending…" : "Suspend"}
                  </Button>
                )}
              </div>
              {(suspend.isError || reactivate.isError || verify.isError || unverify.isError) && (
                <p className="text-sm font-medium text-danger">Couldn&apos;t save. Try again.</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
