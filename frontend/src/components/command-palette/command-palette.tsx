"use client";

import * as React from "react";
import { Command } from "cmdk";
import { useParams, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import {
  Archive,
  BarChart3,
  Briefcase,
  Building2,
  Home,
  LayoutGrid,
  ShieldCheck,
  Sparkles,
  UserSearch,
  Users,
  UsersRound,
  Video,
  type LucideIcon,
} from "lucide-react";

import { Dialog, DialogContent } from "@/components/ui/dialog";
import { useAuth } from "@/lib/auth-context";
import type { Candidate, Project, TalentPoolPoolListItem } from "@/lib/types";

interface NavCommand {
  label: string;
  href: string;
  icon: LucideIcon;
  permission?: string;
}

const NAV_COMMANDS: NavCommand[] = [
  { label: "Home", href: "/home", icon: Home },
  { label: "Jobs", href: "/projects", icon: Briefcase },
  { label: "Candidates", href: "/pipeline", icon: Users, permission: "candidates.view" },
  { label: "Interviews", href: "/interviews", icon: Video, permission: "interviews.view" },
  { label: "Phantom AI", href: "/phantom-ai", icon: Sparkles },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Team", href: "/team", icon: Users },
  { label: "Security", href: "/security", icon: ShieldCheck },
  { label: "Historic Vault", href: "/historic-vault", icon: Archive, permission: "historic_vault.view" },
  { label: "Shadow Jobs", href: "/shadow-jobs", icon: LayoutGrid, permission: "shadow_jobs.view" },
  {
    label: "Phantom Smart Matches",
    href: "/search-candidates",
    icon: UserSearch,
    permission: "shadow_candidates.search",
  },
  {
    label: "Talent Pool",
    href: "/talent-pool",
    icon: UsersRound,
    permission: "talent_pool.view",
  },
  {
    label: "Company Profile",
    href: "/company",
    icon: Building2,
    permission: "company.manage_settings",
  },
];

// cmdk renders each Group's `heading` prop wrapped in a [cmdk-group-heading] element with no
// className hook of its own — style it via a Tailwind arbitrary-descendant selector on the
// Group's own className instead, same idiom accordion.tsx already uses for its chevron icon.
const GROUP_CLASS =
  "[&_[cmdk-group-heading]]:px-2.5 [&_[cmdk-group-heading]]:pb-1.5 [&_[cmdk-group-heading]]:pt-3 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wide [&_[cmdk-group-heading]]:text-muted-foreground first:[&_[cmdk-group-heading]]:pt-1.5";
const ITEM_CLASS =
  "flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-foreground outline-none data-[selected=true]:bg-secondary";

export function CommandPalette({
  open,
  onOpenChange,
  container,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  container?: HTMLElement | null;
}) {
  const router = useRouter();
  const params = useParams<{ id?: string }>();
  const queryClient = useQueryClient();
  const { hasPermission } = useAuth();

  const navCommands = NAV_COMMANDS.filter((cmd) => !cmd.permission || hasPermission(cmd.permission));
  const projects = queryClient.getQueryData<Project[]>(["projects"]) ?? [];
  const projectId = typeof params?.id === "string" ? params.id : undefined;
  const candidates = projectId
    ? queryClient.getQueryData<Candidate[]>(["candidates", { projectId }]) ?? []
    : [];
  const allCandidates = queryClient.getQueryData<Candidate[]>(["candidates", "all"]) ?? [];
  const talentPool = queryClient.getQueryData<TalentPoolPoolListItem[]>(["talent-pool", "mine"]) ?? [];

  const go = (href: string) => {
    onOpenChange(false);
    router.push(href);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent container={container} className="max-w-lg gap-0 overflow-hidden p-0">
        <Command className="flex flex-col" shouldFilter>
          <Command.Input
            placeholder="Search projects, candidates, or jump to a page…"
            className="w-full border-b border-border bg-transparent px-4 py-3.5 pr-10 text-sm text-foreground outline-none placeholder:text-muted-foreground"
          />
          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
              No results found.
            </Command.Empty>

            <Command.Group heading="Navigate" className={GROUP_CLASS}>
              {navCommands.map((cmd) => (
                <Command.Item
                  key={cmd.href}
                  value={cmd.label}
                  onSelect={() => go(cmd.href)}
                  className={ITEM_CLASS}
                >
                  <cmd.icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                  {cmd.label}
                </Command.Item>
              ))}
            </Command.Group>

            {projects.length > 0 && (
              <Command.Group heading="Projects" className={GROUP_CLASS}>
                {projects.map((project) => (
                  <Command.Item
                    key={project.id}
                    value={project.title}
                    onSelect={() => go(`/projects/${project.id}`)}
                    className={ITEM_CLASS}
                  >
                    <Briefcase className="h-4 w-4 shrink-0 text-muted-foreground" />
                    {project.title}
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {candidates.length > 0 && projectId && (
              <Command.Group heading="Candidates in this project" className={GROUP_CLASS}>
                {candidates.map((candidate) => (
                  <Command.Item
                    key={candidate.id}
                    value={`${candidate.callsign} ${candidate.candidate_ref}`}
                    onSelect={() => go(`/projects/${projectId}/candidates/${candidate.id}`)}
                    className={ITEM_CLASS}
                  >
                    <Users className="h-4 w-4 shrink-0 text-muted-foreground" />
                    {candidate.callsign}
                    <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                      {candidate.candidate_ref}
                    </span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {allCandidates.length > 0 && !projectId && (
              <Command.Group heading="Candidates" className={GROUP_CLASS}>
                {allCandidates.map((candidate) => (
                  <Command.Item
                    key={candidate.id}
                    value={`${candidate.callsign} ${candidate.candidate_ref}`}
                    onSelect={() => go(`/projects/${candidate.project_id}/candidates/${candidate.id}`)}
                    className={ITEM_CLASS}
                  >
                    <Users className="h-4 w-4 shrink-0 text-muted-foreground" />
                    {candidate.callsign}
                    <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                      {candidate.candidate_ref}
                    </span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {talentPool.length > 0 && (
              <Command.Group heading="Talent Pool" className={GROUP_CLASS}>
                {talentPool.map((item) => (
                  <Command.Item
                    key={item.id}
                    value={`${item.callsign} ${item.source_role_title}`}
                    onSelect={() => go("/talent-pool")}
                    className={ITEM_CLASS}
                  >
                    <UsersRound className="h-4 w-4 shrink-0 text-muted-foreground" />
                    {item.callsign}
                    <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                      {item.source_role_title}
                    </span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}
          </Command.List>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
