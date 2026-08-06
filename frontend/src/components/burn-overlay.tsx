"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Check, FileText } from "lucide-react";

import { PhantomIcon } from "@/components/phantom-icon";
import { Button } from "@/components/ui/button";
import type { PurgeCertificate } from "@/lib/types";

interface BurnOverlayProps {
  phase: "burning" | "success";
  certificate?: PurgeCertificate | null;
  onContinue?: () => void;
}

// Files fly in from scattered positions around the phantom and get "eaten" — shrinking and
// fading out as they converge on it — staggered so it reads as a sequence, not one flash.
const FILES = [
  { x: -110, y: -70, delay: 0.1 },
  { x: 120, y: -60, delay: 0.35 },
  { x: -130, y: 50, delay: 0.6 },
  { x: 110, y: 70, delay: 0.85 },
  { x: 0, y: -120, delay: 1.1 },
  { x: 0, y: 110, delay: 1.35 },
];

function handleCopyCertificate(certificate: PurgeCertificate) {
  const text = [
    `Purge Certificate — ${certificate.project_title}`,
    `Purged at: ${new Date(certificate.purged_at).toLocaleString()}`,
    `Candidates purged: ${certificate.candidate_count}`,
    "Data categories destroyed:",
    ...certificate.data_categories_destroyed.map((c) => `  - ${c}`),
  ].join("\n");
  void navigator.clipboard.writeText(text);
}

export function BurnOverlay({ phase, certificate, onContinue }: BurnOverlayProps) {
  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 backdrop-blur-sm"
      aria-live="assertive"
    >
      <AnimatePresence mode="wait">
        {phase === "burning" && (
          <motion.div
            key="burning"
            exit={{ opacity: 0 }}
            className="relative flex h-64 w-64 items-center justify-center"
          >
            {FILES.map((file, i) => (
              <motion.div
                key={i}
                initial={{ x: file.x, y: file.y, opacity: 1, scale: 1 }}
                animate={{ x: 0, y: 0, opacity: 0, scale: 0.15 }}
                transition={{ delay: file.delay, duration: 0.5, ease: [0.4, 0, 1, 1] }}
                className="absolute text-white"
              >
                <FileText className="h-7 w-7" strokeWidth={1.75} />
              </motion.div>
            ))}
            <motion.div
              animate={{ y: [0, -10, 0], scale: [1, 1.08, 1] }}
              transition={{ duration: 1.1, repeat: Infinity, ease: "easeInOut" }}
              className="drop-shadow-[0_0_30px_rgba(102,81,176,0.55)]"
            >
              <PhantomIcon className="h-36" />
            </motion.div>
          </motion.div>
        )}
        {phase === "success" && (
          <motion.div
            key="success"
            initial={{ opacity: 0, scale: 0.92, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="flex w-full max-w-md flex-col items-center gap-4 rounded-2xl border border-border bg-white px-10 py-8 shadow-xl shadow-slate-900/10"
          >
            <PhantomIcon className="h-14" />
            <div className="flex items-center gap-2 text-lg font-semibold tracking-tight text-foreground">
              <Check className="h-5 w-5 text-brand" />
              Project successfully purged
            </div>
            {certificate && (
              <div className="flex w-full flex-col gap-2 rounded-xl bg-slate-50 px-4 py-3 text-left">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Purge certificate
                </p>
                <p className="text-sm text-foreground">
                  {certificate.candidate_count} candidate
                  {certificate.candidate_count === 1 ? "" : "s"} and all associated data
                  permanently destroyed:
                </p>
                <ul className="flex flex-col gap-0.5 text-xs text-muted-foreground">
                  {certificate.data_categories_destroyed.map((category) => (
                    <li key={category}>• {category}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="flex gap-2">
              {certificate && (
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => handleCopyCertificate(certificate)}
                >
                  Copy certificate
                </Button>
              )}
              {onContinue && (
                <Button type="button" variant="brand" size="sm" onClick={onContinue}>
                  Continue
                </Button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
