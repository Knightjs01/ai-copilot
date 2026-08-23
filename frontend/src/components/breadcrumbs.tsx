"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, usePathname, useSearchParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { ChevronRight } from "lucide-react";

import { useCandidate } from "@/lib/queries/candidates";
import { useProject } from "@/lib/queries/projects";
import type { CompanyInterviewSummary } from "@/lib/types";

interface Crumb {
  label: string;
  href?: string;
}

// Static top-level destinations, each with the parent hub it belongs to under the new IA (Talent
// Pool/Phantom Smart Talent live under Discover Talent; Team/Company/Security live under Settings;
// Project Vault is its own flat entry, reached from the sidebar's Data group) -- purely
// presentational, no routing change.
const STATIC_CRUMBS: Record<string, Crumb[]> = {
  "/home": [{ label: "Home" }],
  "/projects": [{ label: "Jobs" }],
  "/pipeline": [{ label: "Candidates" }],
  "/talent-pool": [{ label: "Discover Talent", href: "/phantom-ai" }, { label: "Talent Pool" }],
  "/search-candidates": [
    { label: "Discover Talent", href: "/phantom-ai" },
    { label: "Phantom Smart Talent" },
  ],
  "/interviews": [{ label: "Interviews" }],
  "/phantom-ai": [{ label: "Discover Talent" }],
  "/analytics": [{ label: "Analytics" }],
  "/settings": [{ label: "Settings" }],
  "/team": [{ label: "Settings", href: "/settings" }, { label: "Team" }],
  "/company": [{ label: "Settings", href: "/settings" }, { label: "Company Profile" }],
  "/security": [{ label: "Settings", href: "/settings" }, { label: "Security" }],
  "/historic-vault": [{ label: "Project Vault" }],
  "/shadow-jobs": [{ label: "Jobs", href: "/projects" }, { label: "Shadow Jobs" }],
};

const TAB_LABEL: Record<string, string> = {
  overview: "Overview",
  blueprint: "Blueprint",
  candidates: "Candidates",
  interviews: "Interviews",
  activity: "Activity",
  vault: "Identity Vault",
};

export function Breadcrumbs() {
  const pathname = usePathname() ?? "";
  const params = useParams<{ id?: string; candidateId?: string; jobId?: string; interviewId?: string }>();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { data: project } = useProject(
    pathname.startsWith("/projects/") ? params?.id : undefined
  );
  const { data: candidate } = useCandidate(params?.candidateId);

  const crumbs = React.useMemo<Crumb[]>(() => {
    if (STATIC_CRUMBS[pathname]) return STATIC_CRUMBS[pathname];

    if (pathname.startsWith("/interviews/") && params?.interviewId) {
      // Reads the already-fetched company-wide interviews list from cache -- no extra fetch,
      // same convention as the command palette's dynamic groups.
      const interviews = queryClient.getQueryData<CompanyInterviewSummary[]>([
        "interviews",
        "mine-company",
      ]);
      const interview = interviews?.find((i) => i.id === params.interviewId);
      return [
        { label: "Interviews", href: "/interviews" },
        { label: interview?.callsign ?? "Interview" },
      ];
    }

    if (pathname.startsWith("/projects/") && params?.candidateId) {
      return [
        { label: "Jobs", href: "/projects" },
        { label: project?.title ?? "…", href: `/projects/${params.id}` },
        { label: candidate?.callsign ?? "Candidate" },
      ];
    }

    if (pathname.startsWith("/projects/") && params?.id) {
      const tab = searchParams?.get("tab");
      const crumbs: Crumb[] = [
        { label: "Jobs", href: "/projects" },
        { label: project?.title ?? "…" },
      ];
      if (tab && TAB_LABEL[tab]) crumbs.push({ label: TAB_LABEL[tab] });
      return crumbs;
    }

    return [];
  }, [pathname, params, project, candidate, searchParams, queryClient]);

  if (crumbs.length === 0) return <div />;

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-sm">
      {crumbs.map((crumb, i) => (
        <React.Fragment key={`${crumb.label}-${i}`}>
          {i > 0 && <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground/50" />}
          {crumb.href ? (
            <Link
              href={crumb.href}
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              {crumb.label}
            </Link>
          ) : (
            <span className="font-medium text-foreground">{crumb.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}
