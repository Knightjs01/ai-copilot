"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ApiError } from "@/lib/api-client";
import { usePassCandidate } from "@/lib/queries/candidate-search";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { PASS_REASON_LABEL } from "@/lib/status-display";
import type { PassReason } from "@/lib/types";

const PASS_REASONS = Object.keys(PASS_REASON_LABEL) as PassReason[];

export function PassCandidateDialog({
  open,
  onOpenChange,
  jobId,
  callsign,
  onDone,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  jobId: string;
  callsign: string;
  onDone: () => void;
}) {
  const container = useThemeScopeContainer();
  const [reason, setReason] = React.useState<PassReason | undefined>(undefined);
  const [error, setError] = React.useState<string | null>(null);
  const passCandidate = usePassCandidate(jobId);

  const handleSubmit = async () => {
    setError(null);
    try {
      await passCandidate.mutateAsync({ callsign, reason });
      onOpenChange(false);
      setReason(undefined);
      onDone();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Couldn't pass on this candidate. Try again.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent container={container}>
        <DialogHeader>
          <DialogTitle>Pass on {callsign}?</DialogTitle>
          <DialogDescription>
            They&apos;ll no longer appear in search results for this role. This doesn&apos;t notify
            the candidate.
          </DialogDescription>
        </DialogHeader>
        <Select value={reason} onValueChange={(v) => setReason(v as PassReason)}>
          <SelectTrigger>
            <SelectValue placeholder="Reason (optional)" />
          </SelectTrigger>
          <SelectContent container={container}>
            {PASS_REASONS.map((r) => (
              <SelectItem key={r} value={r}>
                {PASS_REASON_LABEL[r]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {error && <p className="text-sm font-medium text-danger">{error}</p>}
        <DialogFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={() => onOpenChange(false)}
            disabled={passCandidate.isPending}
          >
            Cancel
          </Button>
          <Button type="button" variant="danger" onClick={handleSubmit} disabled={passCandidate.isPending}>
            {passCandidate.isPending ? "Passing…" : "Pass"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
