"use client";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { QRCodeSVG } from "qrcode.react";
import { PartyPopper, ShieldCheck, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useMotionVariant } from "@/lib/motion";
import { VERIFICATION_STATUS_LABEL, VERIFICATION_STATUS_VARIANT } from "@/lib/status-display";
import type { VerificationStatus } from "@/lib/types";

interface PassportSuccessOverlayProps {
  active: boolean;
  onDismiss: () => void;
  callsign: string | null;
  headline: string | null;
  verificationStatus: VerificationStatus;
  completionPercentage: number;
  versionNumber: number;
}

export function PassportSuccessOverlay({
  active,
  onDismiss,
  callsign,
  headline,
  verificationStatus,
  completionPercentage,
  versionNumber,
}: PassportSuccessOverlayProps) {
  const cardVariant = useMotionVariant({
    hidden: { opacity: 0, scale: 0.92, y: 12 },
    visible: { opacity: 1, scale: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
  });
  const verifyUrl =
    callsign && typeof window !== "undefined"
      ? `${window.location.origin}/shadow/verify/${callsign}`
      : null;

  return (
    <AnimatePresence>
      {active && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center overflow-y-auto bg-slate-900/60 p-4 backdrop-blur-sm"
          aria-live="assertive"
        >
          <motion.div
            initial="hidden"
            animate="visible"
            variants={cardVariant}
            className="relative flex w-full max-w-md flex-col gap-6 rounded-2xl border-2 border-gold/40 bg-card p-8 shadow-2xl shadow-gold/10"
          >
            <button
              type="button"
              onClick={onDismiss}
              className="absolute right-5 top-5 rounded-full p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="flex flex-col items-center gap-2 text-center">
              <PartyPopper className="h-8 w-8 text-gold" />
              <p className="text-xl font-semibold tracking-tight text-foreground">Success!</p>
              <p className="text-sm text-muted-foreground">
                Your Candidate Passport is now complete.
              </p>
            </div>

            <div className="relative overflow-hidden rounded-2xl border-2 border-gold/40 bg-background p-6">
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-gold to-transparent" />
              <div className="flex flex-col items-center gap-4">
                <div className="flex flex-col items-center gap-1">
                  <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gold">
                    Phantom Passport
                  </span>
                  <p className="text-2xl font-semibold tracking-tight text-foreground">
                    {callsign ?? "—"}
                  </p>
                  {headline && <p className="text-sm text-muted-foreground">{headline}</p>}
                </div>

                {verifyUrl && (
                  <div className="h-32 w-32 shrink-0 rounded-lg border border-border bg-card p-1.5">
                    <QRCodeSVG value={verifyUrl} size={116} className="h-full w-full" />
                  </div>
                )}

                <div className="flex flex-wrap items-center justify-center gap-2">
                  <Badge variant={VERIFICATION_STATUS_VARIANT[verificationStatus]}>
                    <ShieldCheck className="h-3 w-3" />
                    {VERIFICATION_STATUS_LABEL[verificationStatus]}
                  </Badge>
                  <Badge variant="neutral">{completionPercentage}% complete</Badge>
                  <Badge variant="gold">Version {versionNumber}</Badge>
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-2.5">
              <Button asChild variant="brand" size="lg">
                <Link href="/shadow">Take me to the Shadow Job Board</Link>
              </Button>
              <Button asChild variant="secondary">
                <Link href="/shadow/applications">Go to my applications</Link>
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
