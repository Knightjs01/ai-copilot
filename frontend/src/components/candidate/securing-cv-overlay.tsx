"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Check } from "lucide-react";

import { PhantomIcon } from "@/components/phantom-icon";
import { cn } from "@/lib/utils";

// Each step "completes" on its own stagger delay, purely presentational — the real work all
// happens in one blocking request (upload -> redact -> extract), not as discrete server-reported
// stages. The parent pairs this with a MIN_ANIMATION_MS floor (see burn-project-dialog.tsx's
// established pattern) so a fast response never cuts the sequence short; every step here really
// did happen server-side, just not incrementally reported.
const STEPS = [
  { label: "Uploading CV", delay: 0 },
  { label: "Securing personal information", delay: 0.7 },
  { label: "Extracting career information", delay: 1.4 },
  { label: "Building your Passport", delay: 2.1 },
];

export function SecuringCvOverlay({ active }: { active: boolean }) {
  return (
    <AnimatePresence>
      {active && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 backdrop-blur-sm"
          aria-live="assertive"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className="flex w-full max-w-sm flex-col items-center gap-6 rounded-2xl border border-border bg-white px-10 py-8 shadow-xl shadow-slate-900/10"
          >
            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 1.1, repeat: Infinity, ease: "easeInOut" }}
              className="drop-shadow-[0_0_30px_rgba(102,81,176,0.55)]"
            >
              <PhantomIcon className="h-14" />
            </motion.div>
            <div className="text-center">
              <p className="text-lg font-semibold tracking-tight text-foreground">
                Securing your CV
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Phantom is analysing your CV and removing personal information before it becomes
                part of your Passport.
              </p>
            </div>
            <ul className="flex w-full flex-col gap-2.5">
              {STEPS.map((step) => (
                <li key={step.label} className="flex items-center gap-2.5 text-sm">
                  <motion.span
                    initial={{ backgroundColor: "rgb(241 245 249)" }}
                    animate={{ backgroundColor: "rgb(102 81 176)" }}
                    transition={{ delay: step.delay, duration: 0.3 }}
                    className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full"
                  >
                    <motion.span
                      initial={{ opacity: 0, scale: 0.6 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: step.delay + 0.15, duration: 0.2 }}
                    >
                      <Check className="h-3 w-3 text-white" strokeWidth={2.5} />
                    </motion.span>
                  </motion.span>
                  <motion.span
                    initial={{ color: "rgb(100 116 139)" }}
                    animate={{ color: "rgb(15 23 42)" }}
                    transition={{ delay: step.delay, duration: 0.3 }}
                    className={cn("font-medium")}
                  >
                    {step.label}
                  </motion.span>
                </li>
              ))}
            </ul>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
