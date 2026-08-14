"use client";

import { Lock, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

// Fixed categories, not derived per-application — the shared set is always exactly what
// ShadowProfile projects (see backend/app/modules/shadow_jobs/schemas.py) vs. what never leaves
// the Candidate Vault / PassportPersonalInfo, so there's nothing per-job to compute here.
const SHARED = [
  "Professional profile",
  "Relevant career history",
  "Relevant skills",
  "Approved achievements",
  "Relevant qualifications",
];
const PROTECTED = ["Original CV", "Private email", "Private phone number", "Home address", "Other Candidate Vault information"];

export function ApplyDisclosureDialog({
  open,
  onOpenChange,
  onConfirm,
  isSubmitting,
  container,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isSubmitting: boolean;
  // See DialogContent's comment in dialog.tsx — lets the caller (the Shadow job detail page)
  // portal this into its own themed <main> instead of document.body, so the dark obsidian scope
  // reaches the dialog too.
  container?: HTMLElement | null;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent container={container}>
        <DialogHeader>
          <DialogTitle>You&apos;re about to share</DialogTitle>
          <DialogDescription>
            The employer will only receive information you&apos;ve approved for this
            application. Your identity remains private until you choose to reveal it.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-3">
          <ul className="flex flex-col gap-1.5 text-sm text-foreground">
            {SHARED.map((item) => (
              <li key={item} className="flex items-center gap-2">
                <ShieldCheck className="h-3.5 w-3.5 text-success" />
                {item}
              </li>
            ))}
          </ul>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Your private information remains protected
          </p>
          <ul className="flex flex-col gap-1.5 text-sm text-muted-foreground">
            {PROTECTED.map((item) => (
              <li key={item} className="flex items-center gap-2">
                <Lock className="h-3.5 w-3.5" />
                {item}
              </li>
            ))}
          </ul>
        </div>
        <DialogFooter>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button type="button" variant="brand" onClick={onConfirm} disabled={isSubmitting}>
            {isSubmitting ? "Applying…" : "Review & Apply"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
