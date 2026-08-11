"use client";

import * as React from "react";
import { Eye, ShieldAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Field } from "@/components/ui/field";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { useCloseReveal, useRevealIdentity } from "@/lib/queries/identity-vault";
import type { CandidateIdentitySnapshot, RevealReason } from "@/lib/types";

const REASON_OPTIONS: { value: RevealReason; label: string }[] = [
  { value: "Hiring Manager Interview", label: "Hiring Manager Interview" },
  { value: "Offer Preparation", label: "Offer Preparation" },
  { value: "Background Checks", label: "Background Checks" },
  { value: "Client Submission", label: "Client Submission" },
  { value: "Hiring Manager Review", label: "Hiring Manager Review" },
  { value: "Other", label: "Other" },
];

type Phase = "closed" | "confirm" | "snapshot";

function SnapshotRow({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex items-center justify-between border-b border-border pb-2 last:border-0 last:pb-0">
      <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className="font-medium text-foreground">{value ?? "TBC"}</span>
    </div>
  );
}

export function RevealIdentityDialog({ candidateId }: { candidateId: string }) {
  const [phase, setPhase] = React.useState<Phase>("closed");
  const [reason, setReason] = React.useState<RevealReason | null>(null);
  const [snapshot, setSnapshot] = React.useState<CandidateIdentitySnapshot | null>(null);
  const openedAtRef = React.useRef(0);
  const reveal = useRevealIdentity(candidateId);
  const closeReveal = useCloseReveal();

  const handleConfirm = () => {
    if (!reason) return;
    reveal.mutate(reason, {
      onSuccess: (data) => {
        setSnapshot(data);
        openedAtRef.current = Date.now();
        setPhase("snapshot");
      },
    });
  };

  const handleCloseSnapshot = () => {
    if (snapshot) {
      const durationSeconds = Math.round((Date.now() - openedAtRef.current) / 1000);
      closeReveal.mutate({ eventId: snapshot.reveal_event_id, durationSeconds });
    }
    setSnapshot(null);
    setReason(null);
    setPhase("closed");
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setPhase("confirm")}
        title="Reveal Identity"
        className="rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
      >
        <Eye className="h-4 w-4" />
        <span className="sr-only">Reveal Identity</span>
      </button>

      <Dialog open={phase === "confirm"} onOpenChange={(next) => !next && setPhase("closed")}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-brand" />
              Reveal candidate identity
            </DialogTitle>
            <DialogDescription>
              You are about to access confidential candidate information. This action will be
              recorded in the audit log.
            </DialogDescription>
          </DialogHeader>
          <Field label="Reason for access">
            <PillToggleGroup options={REASON_OPTIONS} value={reason} onChange={setReason} />
          </Field>
          {reveal.isError && (
            <p className="mt-2 text-sm font-medium text-danger">
              Couldn&apos;t reveal identity. Try again.
            </p>
          )}
          <DialogFooter>
            <Button type="button" variant="brand" onClick={() => setPhase("closed")}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={handleConfirm}
              disabled={!reason || reveal.isPending}
            >
              {reveal.isPending ? "Revealing…" : "Reveal Identity"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={phase === "snapshot"} onOpenChange={(next) => !next && handleCloseSnapshot()}>
        <DialogContent>
          {snapshot && (
            <>
              <DialogHeader>
                <DialogTitle>Candidate identity snapshot</DialogTitle>
                <DialogDescription>
                  {snapshot.callsign} · {snapshot.candidate_ref}
                </DialogDescription>
              </DialogHeader>
              <div className="flex flex-col gap-3 text-sm">
                <SnapshotRow label="Name" value={snapshot.full_name} />
                <SnapshotRow label="Job title" value={snapshot.current_title} />
                <SnapshotRow label="Current employer" value={snapshot.current_employer} />
                <SnapshotRow label="Location" value={snapshot.location} />
                <SnapshotRow label="Email" value={snapshot.email} />
                <SnapshotRow label="Phone" value={snapshot.phone} />
                <SnapshotRow
                  label="Salary expectations"
                  value={
                    snapshot.expected_salary != null
                      ? `£${snapshot.expected_salary.toLocaleString()}`
                      : null
                  }
                />
                <SnapshotRow label="LinkedIn profile" value={snapshot.linkedin_url} />
                <SnapshotRow label="Original CV" value={snapshot.original_cv_status} />
              </div>
              <DialogFooter>
                <Button type="button" variant="secondary" onClick={handleCloseSnapshot}>
                  Close
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
