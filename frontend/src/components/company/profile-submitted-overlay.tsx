"use client";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { PartyPopper, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useMotionVariant } from "@/lib/motion";

interface ProfileSubmittedOverlayProps {
  active: boolean;
  onDismiss: () => void;
}

export function ProfileSubmittedOverlay({ active, onDismiss }: ProfileSubmittedOverlayProps) {
  const cardVariant = useMotionVariant({
    hidden: { opacity: 0, scale: 0.92, y: 12 },
    visible: { opacity: 1, scale: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } },
  });

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
            className="relative flex w-full max-w-md flex-col gap-6 rounded-2xl border border-border bg-card p-8 shadow-2xl"
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
              <PartyPopper className="h-8 w-8 text-brand" />
              <p className="text-xl font-semibold tracking-tight text-foreground">Success!</p>
              <p className="text-sm text-muted-foreground">
                Your profile has been submitted for review.
              </p>
              <p className="text-sm text-muted-foreground">
                The Phantom team will now review and approve your profile — you&apos;ll receive an
                email once this has been approved.
              </p>
            </div>

            <div className="flex flex-col gap-2.5">
              <Button asChild variant="brand" size="lg">
                <Link href="/projects">Back to home</Link>
              </Button>
              <Button asChild variant="secondary" onClick={onDismiss}>
                <Link href="/company">Stay on my profile</Link>
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
