"use client";

import { motion } from "framer-motion";

import { useMotionVariant } from "@/lib/motion";
import type { MatchTier } from "@/lib/types";

const TIER_STROKE: Record<MatchTier, string> = {
  "Excellent Match": "hsl(var(--success))",
  "Strong Match": "hsl(var(--info))",
  "Potential Match": "hsl(var(--warning))",
  "Weak Match": "hsl(var(--danger))",
};

interface MatchScoreRingProps {
  // Real, server-computed match_score/match_tier -- never a fabricated dimension percentage.
  score: number;
  tier: MatchTier;
  size?: number;
  strokeWidth?: number;
}

export function MatchScoreRing({ score, tier, size = 88, strokeWidth = 6 }: MatchScoreRingProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;

  const ringVariant = useMotionVariant({
    hidden: { strokeDashoffset: circumference },
    visible: { strokeDashoffset: offset, transition: { duration: 0.9, ease: [0.16, 1, 0.3, 1] } },
  });

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="-rotate-90"
        role="img"
        aria-label={`${clamped}% match, ${tier}`}
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="hsl(var(--secondary))"
          strokeWidth={strokeWidth}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={TIER_STROKE[tier]}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial="hidden"
          animate="visible"
          variants={ringVariant}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-semibold text-foreground">{clamped}%</span>
        <span className="text-[9px] font-medium uppercase tracking-wide text-muted-foreground">
          match
        </span>
      </div>
    </div>
  );
}
