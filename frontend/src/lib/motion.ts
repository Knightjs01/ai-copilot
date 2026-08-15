"use client";

import { useReducedMotion, type Variants } from "framer-motion";

export const fadeUpVariant: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } },
};

export const glowPulseVariant: Variants = {
  hidden: { opacity: 0.4 },
  visible: {
    opacity: [0.4, 0.8, 0.4],
    transition: { duration: 3, repeat: Infinity, ease: "easeInOut" },
  },
};

const INSTANT_VARIANT: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.01 } },
};

/** Swaps in an instant, motion-free variant when the user has requested reduced motion. */
export function useMotionVariant(variant: Variants): Variants {
  const reduceMotion = useReducedMotion();
  return reduceMotion ? INSTANT_VARIANT : variant;
}
