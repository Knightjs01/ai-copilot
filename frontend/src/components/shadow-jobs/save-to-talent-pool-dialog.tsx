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
import { useRequestTalentPool } from "@/lib/queries/talent-pool";

export function SaveToTalentPoolDialog({
  jobId,
  applicationId,
  callsign,
}: {
  jobId: string;
  applicationId: string;
  callsign: string;
}) {
  const [open, setOpen] = React.useState(false);
  const [note, setNote] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const requestTalentPool = useRequestTalentPool(jobId, applicationId);

  const handleSubmit = async () => {
    setError(null);
    try {
      await requestTalentPool.mutateAsync(note);
      setOpen(false);
      setNote("");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : "Couldn't send the Talent Pool request. Try again."
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="secondary" size="sm">
          Save to Talent Pool
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Keep {callsign}&apos;s door open</DialogTitle>
          <DialogDescription>
            {callsign} will see this and can choose to allow future matching, decline, or keep
            their profile private — nothing about future access is automatic.
          </DialogDescription>
        </DialogHeader>
        <Textarea
          placeholder="e.g. Strong candidate, would love to consider for future roles"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
        {error && <p className="text-sm font-medium text-danger">{error}</p>}
        <DialogFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setOpen(false)}
            disabled={requestTalentPool.isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="brand"
            onClick={handleSubmit}
            disabled={requestTalentPool.isPending}
          >
            {requestTalentPool.isPending ? "Sending…" : "Send request"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
