"use client";

import { AnimatePresence, motion } from "framer-motion";

interface BurnOverlayProps {
  phase: "burning" | "success";
}

const FLAME_LAYERS = [
  { color: "#7c2d12", delay: 0, duration: 1.1, drift: -18 },
  { color: "#b91c1c", delay: 0.08, duration: 1.05, drift: 14 },
  { color: "#ea580c", delay: 0.16, duration: 1.0, drift: -10 },
  { color: "#f97316", delay: 0.24, duration: 0.95, drift: 8 },
  { color: "#facc15", delay: 0.32, duration: 0.9, drift: 0 },
];

export function BurnOverlay({ phase }: BurnOverlayProps) {
  return (
    <div className="fixed inset-0 z-[100] overflow-hidden" aria-live="assertive">
      {FLAME_LAYERS.map((layer, i) => (
        <motion.div
          key={i}
          initial={{ y: "110%", x: layer.drift, borderRadius: "45% 45% 0 0" }}
          animate={{
            y: "0%",
            x: 0,
            borderRadius: ["45% 45% 0 0", "40% 60% 0 0", "50% 50% 0 0"],
          }}
          transition={{
            y: { delay: layer.delay, duration: layer.duration, ease: [0.16, 1, 0.3, 1] },
            x: { delay: layer.delay, duration: layer.duration, ease: [0.16, 1, 0.3, 1] },
            borderRadius: { delay: layer.delay + layer.duration, duration: 1.6, repeat: Infinity },
          }}
          className="absolute inset-x-[-10%] bottom-0 h-full"
          style={{ backgroundColor: layer.color }}
        />
      ))}
      <AnimatePresence>
        {phase === "success" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="absolute inset-0 flex items-center justify-center"
          >
            <p className="text-2xl font-semibold tracking-tight text-white drop-shadow">
              Project successfully burnt
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
