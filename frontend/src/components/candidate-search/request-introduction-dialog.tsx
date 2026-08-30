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
import { useRequestIntroduction } from "@/lib/queries/shadow-introductions";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";

export function RequestIntroductionDialog({
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
  const [message, setMessage] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const requestIntroduction = useRequestIntroduction(jobId);

  const handleSubmit = async () => {
    setError(null);
    try {
      await requestIntroduction.mutateAsync({ callsign, message });
      onOpenChange(false);
      setMessage("");
      onDone();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : "Couldn't send the introduction request. Try again."
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent container={container}>
        <DialogHeader>
          <DialogTitle>Request an introduction with {callsign}?</DialogTitle>
          <DialogDescription>
            They&apos;ll see this message and can choose to start a conversation — their identity
            stays private unless they decide to share it later.
          </DialogDescription>
        </DialogHeader>
        <Textarea
          placeholder="e.g. We're hiring a Senior Product Designer and think you'd be a great fit — would you be open to a chat?"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        {error && <p className="text-sm font-medium text-danger">{error}</p>}
        <DialogFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={() => onOpenChange(false)}
            disabled={requestIntroduction.isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="brand"
            onClick={handleSubmit}
            disabled={requestIntroduction.isPending}
          >
            {requestIntroduction.isPending ? "Sending…" : "Send request"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
