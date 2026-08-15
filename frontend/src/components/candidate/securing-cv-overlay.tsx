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
            // bg-card, not bg-white — see Card's comment in card.tsx. Static classes here ride
            // whatever scope this component renders inside (e.g. styles/phantom-dark-theme.module.css).
            className="flex w-full max-w-sm flex-col items-center gap-6 rounded-2xl border border-border bg-card px-10 py-8 shadow-xl shadow-slate-900/10"
          >
            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 1.1, repeat: Infinity, ease: "easeInOut" }}
              // Electric-purple glow — matches the shared Phantom Dark palette's --electric accent.
              className="drop-shadow-[0_0_30px_rgba(167,123,244,0.55)]"
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
                  {/* framer-motion's animate prop interpolates literal color strings in JS, not
                      CSS variables — these can't ride the shared theme module's scope the way
                      ordinary Tailwind classes do, so the palette's equivalents are hardcoded
                      directly here. Idle: secondary-panel bg, dim muted label. Completed: brand
                      purple bg, near-white label — matching the shared Phantom Dark palette's
                      --secondary/--brand/--brand-foreground/--foreground. */}
                  <motion.span
                    initial={{ backgroundColor: "rgb(25 31 46)" }}
                    animate={{ backgroundColor: "rgb(148 129 218)" }}
                    transition={{ delay: step.delay, duration: 0.3 }}
                    className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full"
                  >
                    <motion.span
                      initial={{ opacity: 0, scale: 0.6 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: step.delay + 0.15, duration: 0.2 }}
                    >
                      <Check className="h-3 w-3 text-[#0c1322]" strokeWidth={2.5} />
                    </motion.span>
                  </motion.span>
                  <motion.span
                    initial={{ color: "rgb(160 171 187)" }}
                    animate={{ color: "rgb(244 247 250)" }}
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
