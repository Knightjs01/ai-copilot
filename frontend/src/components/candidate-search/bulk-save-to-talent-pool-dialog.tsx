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
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api-client";
import { useBulkRequestTalentPool } from "@/lib/queries/talent-pool";
import { useToast } from "@/lib/toast-context";

export function BulkSaveToTalentPoolDialog({
  open,
  onOpenChange,
  jobId,
  callsigns,
  onDone,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  jobId: string;
  callsigns: string[];
  onDone: () => void;
}) {
  const [note, setNote] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const bulkRequest = useBulkRequestTalentPool();
  const toast = useToast();

  const handleSubmit = async () => {
    setError(null);
    try {
      const result = await bulkRequest.mutateAsync({ jobId, callsigns, note });
      onOpenChange(false);
      setNote("");
      onDone();
      if (result.requested.length > 0) {
        toast({
          title: `Requested ${result.requested.length} candidate${result.requested.length === 1 ? "" : "s"} for Talent Pool`,
          description:
            result.skipped.length > 0
              ? `${result.skipped.length} skipped — already requested or no longer discoverable.`
              : undefined,
          variant: "success",
        });
      } else {
        toast({
          title: "Nothing new to request",
          description: "Every selected candidate was already requested or is no longer discoverable.",
          variant: "default",
        });
      }
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : "Couldn't send the Talent Pool requests. Try again."
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            Save {callsigns.length} candidate{callsigns.length === 1 ? "" : "s"} to Talent Pool
          </DialogTitle>
          <DialogDescription>
            Each candidate will see this request and can choose to allow future matching, decline,
            or keep their profile private — nothing about future access is automatic.
          </DialogDescription>
        </DialogHeader>
        <Textarea
          placeholder="e.g. Strong bench for future roles"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
        {error && <p className="text-sm font-medium text-danger">{error}</p>}
        <DialogFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={() => onOpenChange(false)}
            disabled={bulkRequest.isPending}
          >
            Cancel
          </Button>
          <Button type="button" variant="brand" onClick={handleSubmit} disabled={bulkRequest.isPending}>
            {bulkRequest.isPending ? "Sending…" : "Send requests"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
