"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2 } from "lucide-react";

import { LiveRoleLink } from "@/components/project/live-role-preview";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { ApiError } from "@/lib/api-client";
import { useHiringBlueprint } from "@/lib/queries/hiring-blueprint";
import { useHiringManagerAlignment } from "@/lib/queries/hiring-manager-alignment";
import { usePostToShadow, useSaveAsDraft } from "@/lib/queries/projects";
import { useProjectShadowJob } from "@/lib/queries/shadow-jobs";
import type { Project } from "@/lib/types";

type Step = "choose" | "cancel-confirm" | "posted";

export function ApproveProjectDialog({
  project,
  open,
  onOpenChange,
  hideTrigger,
  description,
}: {
  project: Project;
  // External control lets this same dialog be triggered from somewhere other than its own
  // header button (e.g. "Build my pre-screen kit") without duplicating the readiness-check and
  // post-to-shadow/save-as-draft logic a second time.
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  hideTrigger?: boolean;
  description?: string;
}) {
  const router = useRouter();
  const [internalOpen, setInternalOpen] = React.useState(false);
  const isOpen = open ?? internalOpen;
  const setIsOpen = onOpenChange ?? setInternalOpen;
  const [step, setStep] = React.useState<Step>("choose");
  const [error, setError] = React.useState<string | null>(null);
  const { data: blueprint } = useHiringBlueprint(project.id);
  const { data: alignment } = useHiringManagerAlignment(project.id);
  const { data: shadowJob } = useProjectShadowJob(project.id);
  const postToShadow = usePostToShadow(project.id);
  const saveAsDraft = useSaveAsDraft(project.id);

  const missing: string[] = [];
  if (!project.role_brief) missing.push("a role brief");
  if (!blueprint) missing.push("a Hiring Blueprint");
  if (!alignment) missing.push("Hiring Manager Alignment");
  const isReady = missing.length === 0;

  const goToCandidates = () => router.push(`/projects/${project.id}?tab=candidates`);

  const handleError = (err: unknown) => {
    setError(err instanceof ApiError ? err.detail : "Something went wrong. Try again.");
  };

  const handlePostToShadow = () => {
    setError(null);
    postToShadow.mutate(undefined, {
      onSuccess: () => setStep("posted"),
      onError: handleError,
    });
  };

  const handleSaveAsDraft = () => {
    setError(null);
    saveAsDraft.mutate(undefined, {
      onSuccess: () => {
        setIsOpen(false);
        goToCandidates();
      },
      onError: handleError,
    });
  };

  const handleCancelConfirm = () => {
    setIsOpen(false);
    router.push("/projects");
  };

  const isPending = postToShadow.isPending || saveAsDraft.isPending;

  const trigger = (
    <Button
      size="sm"
      disabled={!isReady}
      onClick={() => {
        setStep("choose");
        setError(null);
        setIsOpen(true);
      }}
    >
      <CheckCircle2 className="h-3.5 w-3.5" />
      Approve
    </Button>
  );

  return (
    <>
      {!hideTrigger &&
        (isReady ? (
          trigger
        ) : (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span tabIndex={0}>{trigger}</span>
              </TooltipTrigger>
              <TooltipContent>Missing {missing.join(", ")}.</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        ))}

      <Dialog open={isOpen} onOpenChange={(next) => !isPending && setIsOpen(next)}>
        <DialogContent className={step === "posted" ? "max-w-3xl" : undefined}>
          {step === "choose" && (
            <>
              <DialogHeader>
                <DialogTitle>Approve &ldquo;{project.title}&rdquo;</DialogTitle>
                <DialogDescription>
                  {description ?? "Choose what happens next for this role."}
                </DialogDescription>
              </DialogHeader>
              {!isReady && (
                <p className="mb-3 rounded-xl bg-warning/15 p-3 text-sm font-medium text-warning-foreground">
                  Missing {missing.join(", ")} — finish those first.
                </p>
              )}
              <div className="flex flex-col gap-3">
                <button
                  type="button"
                  onClick={handlePostToShadow}
                  disabled={isPending || !isReady}
                  className="rounded-xl border border-border p-4 text-left transition-colors hover:border-brand hover:bg-brand/5 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <p className="text-sm font-semibold text-foreground">Post role to Shadow</p>
                  <p className="mt-0.5 text-sm text-muted-foreground">
                    Publishes it publicly with your company profile and opens the candidate
                    pipeline.
                  </p>
                </button>
                <button
                  type="button"
                  onClick={handleSaveAsDraft}
                  disabled={isPending || !isReady}
                  className="rounded-xl border border-border p-4 text-left transition-colors hover:border-muted-foreground hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <p className="text-sm font-semibold text-foreground">Save as draft</p>
                  <p className="mt-0.5 text-sm text-muted-foreground">
                    Opens the candidate pipeline without posting the role publicly.
                  </p>
                </button>
              </div>
              {error && <p className="mt-3 text-sm font-medium text-danger">{error}</p>}
              <DialogFooter>
                <Button
                  type="button"
                  variant="secondary"
                  disabled={isPending}
                  onClick={() => setStep("cancel-confirm")}
                >
                  Cancel
                </Button>
              </DialogFooter>
            </>
          )}

          {step === "cancel-confirm" && (
            <>
              <DialogHeader>
                <DialogTitle>Discard approval?</DialogTitle>
                <DialogDescription>
                  Leave this role unapproved and go back to Projects. Nothing about it changes.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button type="button" variant="secondary" onClick={() => setStep("choose")}>
                  Back
                </Button>
                <Button type="button" variant="brand" onClick={handleCancelConfirm}>
                  Confirm
                </Button>
              </DialogFooter>
            </>
          )}

          {step === "posted" && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-success" />
                  Posted to Shadow
                </DialogTitle>
                <DialogDescription>
                  &ldquo;{project.title}&rdquo; is now live on the public job board.
                </DialogDescription>
              </DialogHeader>
              {shadowJob ? (
                <div className="flex items-center justify-between gap-3 rounded-xl border border-border bg-secondary/40 px-4 py-3">
                  <p className="text-sm text-muted-foreground">
                    This is exactly what candidates see on the public job board.
                  </p>
                  <LiveRoleLink jobId={shadowJob.id} label="Open live role" />
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Loading…</p>
              )}
              <DialogFooter>
                <Button
                  type="button"
                  onClick={() => {
                    setIsOpen(false);
                    goToCandidates();
                  }}
                >
                  Continue to candidates
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
