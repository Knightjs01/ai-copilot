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
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api-client";
import { useRequestReveal } from "@/lib/queries/shadow-reveal";

export function RequestRevealDialog({
  jobId,
  applicationId,
  callsign,
}: {
  jobId: string;
  applicationId: string;
  callsign: string;
}) {
  const [open, setOpen] = React.useState(false);
  const [reason, setReason] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const requestReveal = useRequestReveal(jobId, applicationId);

  const handleSubmit = async () => {
    setError(null);
    try {
      await requestReveal.mutateAsync(reason);
      setOpen(false);
      setReason("");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : "Couldn't send the reveal request. Try again."
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="brand" size="sm">
          Request reveal
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Request identity reveal: {callsign}</DialogTitle>
          <DialogDescription>
            {callsign} will see this reason and can approve or decline. Nothing about their
            identity is disclosed unless they approve.
          </DialogDescription>
        </DialogHeader>
        <Textarea
          placeholder="e.g. Moving to final interview"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        {error && <p className="text-sm font-medium text-danger">{error}</p>}
        <DialogFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setOpen(false)}
            disabled={requestReveal.isPending}
          >
            Cancel
          </Button>
          <Button type="button" variant="brand" onClick={handleSubmit} disabled={requestReveal.isPending}>
            {requestReveal.isPending ? "Sending…" : "Send request"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
