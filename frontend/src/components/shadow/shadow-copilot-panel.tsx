"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Send, Sparkles, X } from "lucide-react";

import { useShadowCopilot } from "@/components/shadow/shadow-copilot-provider";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import type { CopilotContextType } from "@/lib/types";

const QUICK_PROMPTS: Partial<Record<CopilotContextType, { label: string; message: string }[]>> = {
  job: [{ label: "Explain my match", message: "How well do I match this role?" }],
  passport: [{ label: "Improve my summary", message: "How can I improve my summary?" }],
  application: [
    { label: "Summarize my applications", message: "What's the status of my applications?" },
  ],
  interview: [{ label: "Help me prepare", message: "Help me prepare for this interview." }],
};

// A right-edge slide-over, not the shared Dialog primitive -- DialogContent is capped at
// max-w-lg (a centered confirm-dialog footprint), too narrow for a scrolling conversation, same
// finding Phase 3 already made for Messages. Built directly on DialogPrimitive so it can be a
// full-height edge panel instead.
export function ShadowCopilotPanel() {
  const { isOpen, close, messages, isSending, error, sendMessage, context } = useShadowCopilot();
  const [draft, setDraft] = React.useState("");
  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isSending]);

  const handleSend = () => {
    if (!draft.trim() || isSending) return;
    sendMessage(draft);
    setDraft("");
  };

  const prompts = QUICK_PROMPTS[context.type] ?? [];

  return (
    <DialogPrimitive.Root open={isOpen} onOpenChange={(open) => !open && close()}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-[120] bg-slate-900/40 backdrop-blur-[2px] data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content className="fixed inset-y-0 right-0 z-[120] flex h-full w-full flex-col border-l border-border bg-card data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 sm:w-[420px]">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-brand" />
              <DialogPrimitive.Title className="text-sm font-semibold text-foreground">
                Phantom AI
              </DialogPrimitive.Title>
            </div>
            <DialogPrimitive.Close className="rounded-full p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground">
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </DialogPrimitive.Close>
          </div>

          <div
            ref={scrollRef}
            role="log"
            aria-live="polite"
            className="flex-1 overflow-y-auto px-5 py-4"
          >
            {messages.length === 0 && (
              <div className="flex flex-col gap-3">
                <p className="text-sm text-muted-foreground">
                  Ask me to search jobs, explain a match, improve your Passport, check your
                  applications, or prep for an interview.
                </p>
                {prompts.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {prompts.map((prompt) => (
                      <button
                        key={prompt.label}
                        type="button"
                        onClick={() => sendMessage(prompt.message)}
                        className="rounded-full border border-border px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary"
                      >
                        {prompt.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="flex flex-col gap-3">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex flex-col gap-1",
                    message.role === "user" ? "items-end" : "items-start"
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[85%] whitespace-pre-line rounded-2xl px-4 py-2.5 text-sm",
                      message.role === "user"
                        ? "bg-brand text-brand-foreground"
                        : "bg-secondary text-foreground"
                    )}
                  >
                    {message.content}
                  </div>
                </div>
              ))}
              {isSending && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Spinner className="h-4 w-4" />
                  Thinking…
                </div>
              )}
              {error && <p className="text-sm font-medium text-danger">{error}</p>}
            </div>
          </div>

          <div className="flex items-end gap-2 border-t border-border p-4">
            <Textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask Phantom AI…"
              rows={1}
              className="min-h-0 flex-1 resize-none py-2.5"
            />
            <Button
              type="button"
              size="icon"
              onClick={handleSend}
              disabled={!draft.trim() || isSending}
              aria-label="Send message"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
