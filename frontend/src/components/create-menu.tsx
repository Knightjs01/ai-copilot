"use client";

import * as React from "react";
import { Plus, UserPlus } from "lucide-react";

import { InviteTeammateDialog } from "@/components/invite-teammate-dialog";
import { NewProjectDialog } from "@/components/new-project-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

// Scoped to the two entry points that work context-free (create a job, invite a teammate).
// "Add candidate" / "Schedule interview" need a project/applicant context a global button on an
// arbitrary page doesn't have, so they stay exactly where they already are.
export function CreateMenu({
  collapsed,
  container,
}: {
  collapsed?: boolean;
  container?: HTMLElement | null;
}) {
  const { hasPermission } = useAuth();
  const [showNewProject, setShowNewProject] = React.useState(false);
  const [showInvite, setShowInvite] = React.useState(false);
  const canInvite = hasPermission("users.invite");

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            className={cn(
              "flex items-center justify-center gap-2 rounded-lg bg-brand px-3 py-2 text-sm font-medium text-brand-foreground transition-colors hover:opacity-90",
              collapsed && "px-0"
            )}
            aria-label="Create"
          >
            <Plus className="h-4 w-4 shrink-0" />
            {!collapsed && "Create"}
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent container={container} align="start" side={collapsed ? "right" : "top"}>
          <DropdownMenuItem onSelect={() => setShowNewProject(true)}>
            <Plus className="h-3.5 w-3.5" />
            Create job
          </DropdownMenuItem>
          {canInvite && (
            <DropdownMenuItem onSelect={() => setShowInvite(true)}>
              <UserPlus className="h-3.5 w-3.5" />
              Invite teammate
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <NewProjectDialog open={showNewProject} onOpenChange={setShowNewProject} hideTrigger />
      {canInvite && (
        <InviteTeammateDialog open={showInvite} onOpenChange={setShowInvite} hideTrigger />
      )}
    </>
  );
}
