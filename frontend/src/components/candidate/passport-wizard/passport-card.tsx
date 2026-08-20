"use client";

import { QRCodeSVG } from "qrcode.react";
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
// exactly the premium/status moment the palette is reserved for. The QR code is real: it encodes
// a link to the public /shadow/verify/{callsign} page, not a decorative pattern -- see
// PhantomPassportService.get_verification_by_callsign on the backend.
export function PassportCard({
  callsign,
  headline,
  verificationStatus,
  completionPercentage,
  versionNumber,
}: PassportCardProps) {
  const verifyUrl =
    callsign && typeof window !== "undefined"
      ? `${window.location.origin}/shadow/verify/${callsign}`
      : null;

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
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-1">
            <p className="text-2xl font-semibold tracking-tight text-foreground">
              {callsign ?? "—"}
            </p>
            {headline && <p className="text-sm text-muted-foreground">{headline}</p>}
          </div>
          {verifyUrl && (
            <div className="shrink-0 rounded-lg border border-border bg-background p-1.5">
              <QRCodeSVG value={verifyUrl} size={64} />
            </div>
          )}
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
          Reveal Request. Scan the code to open your public verification page.
        </p>
      </div>
    </div>
  );
}
