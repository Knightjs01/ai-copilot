"use client";

import * as React from "react";
import Link from "next/link";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";

export interface MobileNavGroup {
  label: string;
  links: { href: string; label: string }[];
}

// A full-bleed edge drawer, not the centered-modal Dialog primitive — that primitive's overlay
// + centered-card layout doesn't fit a slide-in nav panel, so this is a small purpose-built
// overlay instead of stretching Dialog to do something it wasn't shaped for.
export function MobileNav({
  open,
  onOpenChange,
  groups,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  groups: MobileNavGroup[];
}) {
  const reduceMotion = useReducedMotion();
  const closeButtonRef = React.useRef<HTMLButtonElement>(null);

  React.useEffect(() => {
    if (!open) return;

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onOpenChange(false);
    };
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onOpenChange]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex flex-col bg-background md:hidden"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.2 }}
          role="dialog"
          aria-modal="true"
          aria-label="Site navigation"
        >
          <div className="flex h-16 shrink-0 items-center justify-between border-b border-border px-6">
            <span className="text-sm font-medium text-muted-foreground">Menu</span>
            <Button
              ref={closeButtonRef}
              variant="ghost"
              size="icon"
              aria-label="Close menu"
              onClick={() => onOpenChange(false)}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-8">
            <div className="flex flex-col gap-8">
              {groups.map((group) => (
                <div key={group.label} className="flex flex-col gap-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    {group.label}
                  </p>
                  <div className="flex flex-col gap-1">
                    {group.links.map((link) => (
                      <Link
                        key={link.href}
                        href={link.href}
                        onClick={() => onOpenChange(false)}
                        className="rounded-xl px-3 py-2.5 text-lg font-medium text-foreground transition-colors hover:bg-secondary"
                      >
                        {link.label}
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex shrink-0 flex-col gap-3 border-t border-border px-6 py-6">
            <Link
              href="/login"
              onClick={() => onOpenChange(false)}
              className="text-center text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Log in
            </Link>
            <Button asChild variant="secondary" size="lg" onClick={() => onOpenChange(false)}>
              <Link href="/shadow/signup">Create Passport</Link>
            </Button>
            <Button asChild variant="brand" size="lg" onClick={() => onOpenChange(false)}>
              <Link href="/signup">Start hiring</Link>
            </Button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
