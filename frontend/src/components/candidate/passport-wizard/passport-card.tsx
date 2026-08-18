"use client";

import { ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { VERIFICATION_STATUS_LABEL, VERIFICATION_STATUS_VARIANT } from "@/lib/status-display";
import type { VerificationStatus } from "@/lib/types";

interface PassportCardProps {
  callsign: string | null;
  headline: string | null;
  verificationStatus: VerificationStatus;
  completionPercentage: number;
  versionNumber: number;
}

// The final "digital credential" reveal — gold accents, used selectively here because this is
// exactly the premium/status moment the palette is reserved for. Real fields only: no QR code
// (nothing real to scan), no invented authentication tier beyond the real 3-state verification
// field.
export function PassportCard({
  callsign,
  headline,
  verificationStatus,
  completionPercentage,
  versionNumber,
}: PassportCardProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl border-2 border-gold/40 bg-card p-6 shadow-lg shadow-gold/10">
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-gold to-transparent" />
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-3">
          <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gold">
            Phantom Passport
          </span>
          <Badge variant="gold">Version {versionNumber}</Badge>
        </div>
        <div className="flex flex-col gap-1">
          <p className="text-2xl font-semibold tracking-tight text-foreground">
            {callsign ?? "—"}
          </p>
          {headline && <p className="text-sm text-muted-foreground">{headline}</p>}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={VERIFICATION_STATUS_VARIANT[verificationStatus]}>
            <ShieldCheck className="h-3 w-3" />
            {VERIFICATION_STATUS_LABEL[verificationStatus]}
          </Badge>
          <Badge variant="neutral">{completionPercentage}% complete</Badge>
        </div>
        <p className="text-xs text-muted-foreground">
          This is your Callsign — the only identity companies see until you personally approve a
          Reveal Request.
        </p>
      </div>
    </div>
  );
}
