"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2 } from "lucide-react";

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
import type { Project } from "@/lib/types";

type Step = "choose" | "cancel-confirm";

export function ApproveProjectDialog({ project }: { project: Project }) {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);
  const [step, setStep] = React.useState<Step>("choose");
  const [error, setError] = React.useState<string | null>(null);
  const { data: blueprint } = useHiringBlueprint(project.id);
  const { data: alignment } = useHiringManagerAlignment(project.id);
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
      onSuccess: () => {
        setOpen(false);
        goToCandidates();
      },
      onError: handleError,
    });
  };

  const handleSaveAsDraft = () => {
    setError(null);
    saveAsDraft.mutate(undefined, {
      onSuccess: () => {
        setOpen(false);
        goToCandidates();
      },
      onError: handleError,
    });
  };

  const handleCancelConfirm = () => {
    setOpen(false);
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
        setOpen(true);
      }}
    >
      <CheckCircle2 className="h-3.5 w-3.5" />
      Approve
    </Button>
  );

  return (
    <>
      {isReady ? (
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
      )}

      <Dialog open={open} onOpenChange={(next) => !isPending && setOpen(next)}>
        <DialogContent>
          {step === "choose" ? (
            <>
              <DialogHeader>
                <DialogTitle>Approve &ldquo;{project.title}&rdquo;</DialogTitle>
                <DialogDescription>
                  Choose what happens next for this role.
                </DialogDescription>
              </DialogHeader>
              <div className="flex flex-col gap-3">
                <button
                  type="button"
                  onClick={handlePostToShadow}
                  disabled={isPending}
                  className="rounded-xl border border-border p-4 text-left transition-colors hover:border-brand hover:bg-brand/5 disabled:opacity-60"
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
                  disabled={isPending}
                  className="rounded-xl border border-border p-4 text-left transition-colors hover:border-muted-foreground hover:bg-secondary disabled:opacity-60"
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
          ) : (
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
        </DialogContent>
      </Dialog>
    </>
  );
}
