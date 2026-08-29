"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { usePublishChanges } from "@/lib/queries/company";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { useToast } from "@/lib/toast-context";

// Company Onboarding Phase 2 -- publishing from an already-live profile no longer goes through
// staff review (see CompanyService.self_publish_changes); this dialog is the one real
// confirmation step left, matching the user's own "as long as they check a box to approve
// changes" requirement. The checkbox is enforced server-side too, not just here.
export function PublishChangesDialog() {
  const [open, setOpen] = React.useState(false);
  const [confirmed, setConfirmed] = React.useState(false);
  const publish = usePublishChanges();
  const container = useThemeScopeContainer();
  const toast = useToast();

  const handlePublish = async () => {
    await publish.mutateAsync();
    setOpen(false);
    setConfirmed(false);
    toast({ title: "Changes published", variant: "success" });
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setConfirmed(false);
      }}
    >
      <DialogTrigger asChild>
        <Button type="button" variant="brand" size="sm">
          Publish changes
        </Button>
      </DialogTrigger>
      <DialogContent container={container}>
        <DialogHeader>
          <DialogTitle>Publish changes</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            This updates what candidates see on your public profile immediately — no Phantom
            review needed.
          </p>
          <label className="flex items-center gap-2 text-sm text-foreground">
            <input
              type="checkbox"
              className="accent-brand"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            I approve these changes
          </label>
          {publish.isError && (
            <p className="text-sm font-medium text-danger">
              Couldn&apos;t publish. Try again.
            </p>
          )}
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setOpen(false)}
            disabled={publish.isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="brand"
            onClick={handlePublish}
            disabled={!confirmed || publish.isPending}
          >
            {publish.isPending ? "Publishing…" : "Publish"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
