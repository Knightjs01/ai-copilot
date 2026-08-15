"use client";

import * as React from "react";

export type ToastVariant = "default" | "success" | "danger";

export interface ToastEntry {
  id: string;
  title: string;
  description?: string;
  variant: ToastVariant;
}

interface ToastInput {
  title: string;
  description?: string;
  variant?: ToastVariant;
}

interface ToastQueueContextValue {
  toasts: ToastEntry[];
  addToast: (input: ToastInput) => void;
  dismissToast: (id: string) => void;
}

const ToastQueueContext = React.createContext<ToastQueueContextValue | null>(null);

const AUTO_DISMISS_MS = 5000;

export function ToastQueueProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastEntry[]>([]);

  const dismissToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = React.useCallback(
    ({ title, description, variant = "default" }: ToastInput) => {
      const id = crypto.randomUUID();
      setToasts((prev) => [...prev, { id, title, description, variant }]);
      window.setTimeout(() => dismissToast(id), AUTO_DISMISS_MS);
    },
    [dismissToast]
  );

  const value = React.useMemo(
    () => ({ toasts, addToast, dismissToast }),
    [toasts, addToast, dismissToast]
  );

  return <ToastQueueContext.Provider value={value}>{children}</ToastQueueContext.Provider>;
}

export function useToast() {
  const ctx = React.useContext(ToastQueueContext);
  if (!ctx) throw new Error("useToast must be used within ToastQueueProvider");
  return ctx.addToast;
}

export function useToastQueue() {
  const ctx = React.useContext(ToastQueueContext);
  if (!ctx) throw new Error("useToastQueue must be used within ToastQueueProvider");
  return ctx;
}
