"use client";

import { Command } from "cmdk";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import {
  Bookmark,
  Briefcase,
  CalendarClock,
  Compass,
  Home,
  IdCard,
  MessageSquare,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import { Dialog, DialogContent } from "@/components/ui/dialog";
import type {
  CandidateInterviewSummary,
  MessageThreadSummary,
  SavedShadowJob,
  ShadowApplication,
} from "@/lib/types";

interface NavCommand {
  label: string;
  href: string;
  icon: LucideIcon;
}

const NAV_COMMANDS: NavCommand[] = [
  { label: "Home", href: "/shadow/home", icon: Home },
  { label: "Discover", href: "/shadow", icon: Compass },
  { label: "For You", href: "/shadow/for-you", icon: Sparkles },
  { label: "Applications", href: "/shadow/applications", icon: Briefcase },
  { label: "Messages", href: "/shadow/messages", icon: MessageSquare },
  { label: "Interviews", href: "/shadow/interviews", icon: CalendarClock },
  { label: "My Passport", href: "/shadow/passport", icon: IdCard },
  { label: "Saved Jobs", href: "/shadow/saved-jobs", icon: Bookmark },
];

// Same styling idiom as the ATS command palette (command-palette/command-palette.tsx) — kept as
// its own component rather than shared, since the destinations/data are entirely different
// (candidate-facing, not recruiter-facing) even though the shell is identical.
const GROUP_CLASS =
  "[&_[cmdk-group-heading]]:px-2.5 [&_[cmdk-group-heading]]:pb-1.5 [&_[cmdk-group-heading]]:pt-3 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wide [&_[cmdk-group-heading]]:text-muted-foreground first:[&_[cmdk-group-heading]]:pt-1.5";
const ITEM_CLASS =
  "flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-foreground outline-none data-[selected=true]:bg-secondary";

export function ShadowCommandPalette({
  open,
  onOpenChange,
  container,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  container?: HTMLElement | null;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const savedJobs = queryClient.getQueryData<SavedShadowJob[]>(["saved-jobs", "all"]) ?? [];
  const applications =
    queryClient.getQueryData<ShadowApplication[]>(["shadow-jobs", "applications", "me"]) ?? [];
  const messageThreads =
    queryClient.getQueryData<MessageThreadSummary[]>(["messages", "threads"]) ?? [];
  const interviews =
    queryClient.getQueryData<CandidateInterviewSummary[]>(["interviews", "mine"]) ?? [];

  const go = (href: string) => {
    onOpenChange(false);
    router.push(href);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent container={container} className="max-w-lg gap-0 overflow-hidden p-0">
        <Command className="flex flex-col" shouldFilter>
          <Command.Input
            placeholder="Search your applications, saved jobs, or jump to a page…"
            className="w-full border-b border-border bg-transparent px-4 py-3.5 pr-10 text-sm text-foreground outline-none placeholder:text-muted-foreground"
          />
          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
              No results found.
            </Command.Empty>

            <Command.Group heading="Navigate" className={GROUP_CLASS}>
              {NAV_COMMANDS.map((cmd) => (
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

            {applications.length > 0 && (
              <Command.Group heading="Your applications" className={GROUP_CLASS}>
                {applications.map((application) => (
                  <Command.Item
                    key={application.id}
                    value={`${application.job_title} ${application.company_name}`}
                    onSelect={() => go(`/shadow/applications/${application.id}`)}
                    className={ITEM_CLASS}
                  >
                    <Briefcase className="h-4 w-4 shrink-0 text-muted-foreground" />
                    {application.job_title}
                    <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                      {application.company_name}
                    </span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {messageThreads.length > 0 && (
              <Command.Group heading="Your conversations" className={GROUP_CLASS}>
                {messageThreads.map((thread) => (
                  <Command.Item
                    key={thread.application_id}
                    value={`${thread.job_title} ${thread.company_name}`}
                    onSelect={() => go(`/shadow/messages/${thread.application_id}`)}
                    className={ITEM_CLASS}
                  >
                    <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
                    {thread.job_title}
                    <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                      {thread.company_name}
                    </span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {interviews.length > 0 && (
              <Command.Group heading="Your interviews" className={GROUP_CLASS}>
                {interviews.map((interview) => (
                  <Command.Item
                    key={interview.id}
                    value={`${interview.job_title} ${interview.company_name}`}
                    onSelect={() => go("/shadow/interviews")}
                    className={ITEM_CLASS}
                  >
                    <CalendarClock className="h-4 w-4 shrink-0 text-muted-foreground" />
                    {interview.job_title}
                    <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                      {interview.company_name}
                    </span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {savedJobs.length > 0 && (
              <Command.Group heading="Saved jobs" className={GROUP_CLASS}>
                {savedJobs.map((saved) => (
                  <Command.Item
                    key={saved.id}
                    value={`${saved.job.title} ${saved.job.company_name}`}
                    onSelect={() => go(`/shadow/jobs/${saved.job.id}`)}
                    className={ITEM_CLASS}
                  >
                    <Bookmark className="h-4 w-4 shrink-0 text-muted-foreground" />
                    {saved.job.title}
                    <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                      {saved.job.company_name}
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
