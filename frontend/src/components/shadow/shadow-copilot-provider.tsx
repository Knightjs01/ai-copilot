"use client";

import * as React from "react";
import { Sparkles } from "lucide-react";

import { ShadowCopilotPanel } from "@/components/shadow/shadow-copilot-panel";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { useSendCopilotMessage } from "@/lib/queries/copilot";
import type { CopilotContextType, CopilotMessage } from "@/lib/types";

export interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface CopilotPageContext {
  type: CopilotContextType;
  id?: string;
}

interface ShadowCopilotContextValue {
  isOpen: boolean;
  messages: DisplayMessage[];
  isSending: boolean;
  error: string | null;
  context: CopilotPageContext;
  open: (context?: CopilotPageContext) => void;
  close: () => void;
  setContext: (context: CopilotPageContext) => void;
  sendMessage: (text: string) => void;
}

const ShadowCopilotContext = React.createContext<ShadowCopilotContextValue | null>(null);

// Capped, matches the backend's own CopilotChatRequest.history max_length=10 — no point sending
// more than the server will read.
const HISTORY_LIMIT = 10;

// Mounted once in app/shadow/layout.tsx -- the OUTER layout, not (candidate)/layout.tsx, since
// job detail lives outside that route group and must still get the co-pilot. Always provides
// the context (setContext calls from a logged-out visitor's job-detail view are harmless
// no-ops), but only renders the trigger/panel UI for an authenticated candidate.
export function ShadowCopilotProvider({ children }: { children: React.ReactNode }) {
  const { candidate } = useCandidateAuth();
  const [isOpen, setIsOpen] = React.useState(false);
  const [context, setContextState] = React.useState<CopilotPageContext>({ type: "none" });
  const [messages, setMessages] = React.useState<DisplayMessage[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const sendCopilotMessage = useSendCopilotMessage();

  const open = React.useCallback((ctx?: CopilotPageContext) => {
    if (ctx) setContextState(ctx);
    setIsOpen(true);
  }, []);
  const close = React.useCallback(() => setIsOpen(false), []);
  const setContext = React.useCallback((ctx: CopilotPageContext) => setContextState(ctx), []);

  const sendMessage = React.useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;
      setError(null);
      const userMessage: DisplayMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
      };
      const history: CopilotMessage[] = messages
        .slice(-HISTORY_LIMIT)
        .map((m) => ({ role: m.role, content: m.content }));
      setMessages((prev) => [...prev, userMessage]);

      sendCopilotMessage.mutate(
        {
          message: trimmed,
          context_type: context.type,
          context_id: context.id ?? null,
          history,
        },
        {
          onSuccess: (data) => {
            setMessages((prev) => [
              ...prev,
              { id: crypto.randomUUID(), role: "assistant", content: data.reply },
            ]);
          },
          onError: () => {
            setError("Phantom AI couldn't respond right now. Try again.");
          },
        }
      );
    },
    [context, messages, sendCopilotMessage]
  );

  const value = React.useMemo<ShadowCopilotContextValue>(
    () => ({
      isOpen,
      messages,
      isSending: sendCopilotMessage.isPending,
      error,
      context,
      open,
      close,
      setContext,
      sendMessage,
    }),
    [
      isOpen,
      messages,
      sendCopilotMessage.isPending,
      error,
      context,
      open,
      close,
      setContext,
      sendMessage,
    ]
  );

  return (
    <ShadowCopilotContext.Provider value={value}>
      {children}
      {candidate && (
        <>
          <button
            type="button"
            onClick={() => open()}
            aria-label="Open Phantom AI"
            className="fixed bottom-20 right-4 z-[110] flex h-12 w-12 items-center justify-center rounded-full bg-brand text-brand-foreground shadow-xl shadow-slate-900/20 transition-transform hover:scale-105 md:bottom-6"
          >
            <Sparkles className="h-5 w-5" />
          </button>
          <ShadowCopilotPanel />
        </>
      )}
    </ShadowCopilotContext.Provider>
  );
}

export function useShadowCopilot() {
  const ctx = React.useContext(ShadowCopilotContext);
  if (!ctx) throw new Error("useShadowCopilot must be used within ShadowCopilotProvider");
  return ctx;
}
