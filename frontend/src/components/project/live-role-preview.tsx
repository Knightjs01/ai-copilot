"use client";

import * as React from "react";
import { ExternalLink, Eye } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

// The most honest "preview" is the real public page itself, in an iframe -- not a second,
// hand-built rendering that could quietly drift from what candidates actually see. Same-origin
// (Shadow lives in the same Next.js app as the ATS), and this app sets no X-Frame-Options/CSP
// that would block it.
export function LiveRolePreviewFrame({ jobId }: { jobId: string }) {
  const publicUrl = `/shadow/jobs/${jobId}`;
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          This is exactly what candidates see on the public job board.
        </p>
        <a
          href={publicUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex shrink-0 items-center gap-1 text-xs font-medium text-brand hover:underline"
        >
          Open in new tab
          <ExternalLink className="h-3 w-3" />
        </a>
      </div>
      <div className="h-[55vh] w-full overflow-hidden rounded-xl border border-border">
        <iframe src={publicUrl} title="Live role preview" className="h-full w-full" />
      </div>
    </div>
  );
}

export function LiveRolePreviewDialog({
  jobId,
  open,
  onOpenChange,
  hideTrigger,
}: {
  jobId: string;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  hideTrigger?: boolean;
}) {
  const [internalOpen, setInternalOpen] = React.useState(false);
  const isOpen = open ?? internalOpen;
  const setIsOpen = onOpenChange ?? setInternalOpen;

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      {!hideTrigger && (
        <DialogTrigger asChild>
          <Button type="button" variant="secondary" size="sm">
            <Eye className="h-3.5 w-3.5" />
            View live role
          </Button>
        </DialogTrigger>
      )}
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Live role preview</DialogTitle>
        </DialogHeader>
        <LiveRolePreviewFrame jobId={jobId} />
      </DialogContent>
    </Dialog>
  );
}
