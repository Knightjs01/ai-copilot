"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { BurnOverlay } from "@/components/burn-overlay";
import { PhantomIcon } from "@/components/phantom-icon";
import { StepUpDialog } from "@/components/step-up-dialog";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useBurnProject } from "@/lib/queries/project-deletion";
import type { PurgeCertificate } from "@/lib/types";

// Minimum time the purge animation plays before the API result is allowed to flip it to the
// success state — an instant response shouldn't cut the animation short.
const MIN_ANIMATION_MS = 1400;

type Phase = "idle" | "burning" | "success";

export function BurnProjectDialog({
  projectId,
  projectTitle,
}: {
  projectId: string;
  projectTitle: string;
}) {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);
  const [stepUpOpen, setStepUpOpen] = React.useState(false);
  const [phase, setPhase] = React.useState<Phase>("idle");
  const [error, setError] = React.useState<string | null>(null);
  const [certificate, setCertificate] = React.useState<PurgeCertificate | null>(null);
  const burnProject = useBurnProject(projectId);

  const handleRequestConfirm = () => {
    setOpen(false);
    setStepUpOpen(true);
  };

  const handleVerified = async (stepUpToken: string) => {
    setError(null);
    setPhase("burning");
    const minDelay = new Promise((resolve) => setTimeout(resolve, MIN_ANIMATION_MS));
    try {
      const [result] = await Promise.all([burnProject.mutateAsync(stepUpToken), minDelay]);
      setCertificate(result.certificate);
      setPhase("success");
    } catch {
      setPhase("idle");
      setError("Couldn't purge this project. Try again.");
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={(next) => phase === "idle" && setOpen(next)}>
        <DialogTrigger asChild>
          <Button variant="brand" size="sm">
            <PhantomIcon className="brightness-0 invert" />
            Purge my project
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Purge &ldquo;{projectTitle}&rdquo;?</DialogTitle>
            <DialogDescription>
              Permanently deletes this project and every candidate under it: resumes, AI notes,
              assessments, everything. This can&apos;t be undone. Typically done once a role is
              closed, to keep the platform GDPR-compliant.
            </DialogDescription>
          </DialogHeader>
          {error && <p className="text-sm font-medium text-danger">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="button" variant="brand" onClick={handleRequestConfirm}>
              <PhantomIcon className="brightness-0 invert" />
              Purge this project
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <StepUpDialog
        open={stepUpOpen}
        onOpenChange={setStepUpOpen}
        title="Confirm it's you"
        description="Purging a project is permanent — re-enter your password to continue."
        onVerified={handleVerified}
      />
      {phase !== "idle" && (
        <BurnOverlay
          phase={phase}
          certificate={certificate}
          onContinue={phase === "success" ? () => router.push("/projects") : undefined}
        />
      )}
    </>
  );
}
