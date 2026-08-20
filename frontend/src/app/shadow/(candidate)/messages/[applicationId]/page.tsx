"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { useMessageThread, useSendCandidateMessage } from "@/lib/queries/messages";
import { cn } from "@/lib/utils";

export default function MessageThreadPage() {
  const params = useParams<{ applicationId: string }>();
  const { data: thread, isLoading } = useMessageThread(params.applicationId);
  const sendMessage = useSendCandidateMessage(params.applicationId);
  const [body, setBody] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);

  const companyLabel = thread?.messages.find((m) => m.sender_type === "company")?.sender_label;

  const handleSend = () => {
    const trimmed = body.trim();
    if (!trimmed) return;
    setError(null);
    sendMessage.mutate(trimmed, {
      onSuccess: () => setBody(""),
      onError: () => setError("Couldn't send message. Try again."),
    });
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link
          href="/shadow/messages"
          className="mb-3 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to messages
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {companyLabel ?? "Messages"}
        </h1>
      </div>

      <Card>
        <CardContent className="flex flex-col gap-4 py-5">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner className="h-6 w-6 text-muted-foreground" />
            </div>
          ) : thread && thread.messages.length > 0 ? (
            <div role="log" aria-live="polite" className="flex flex-col gap-3">
              {thread.messages.map((message) => (
                <div
                  key={message.id}
                  className={cn("flex flex-col gap-1", message.is_mine ? "items-end" : "items-start")}
                >
                  <span className="text-xs text-muted-foreground">{message.sender_label}</span>
                  <div
                    className={cn(
                      "max-w-[85%] rounded-2xl px-4 py-2.5 text-sm sm:max-w-[75%]",
                      message.is_mine
                        ? "bg-brand text-brand-foreground"
                        : "bg-secondary text-foreground"
                    )}
                  >
                    {message.body}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 py-12 text-center">
              <p className="text-sm font-medium text-foreground">No messages yet</p>
              <p className="max-w-xs text-sm text-muted-foreground">
                Send a message to start the conversation.
              </p>
            </div>
          )}

          <div className="flex flex-col gap-2 border-t border-border pt-4">
            <Textarea
              placeholder="Write a message…"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              disabled={sendMessage.isPending}
            />
            {error && <p className="text-sm font-medium text-danger">{error}</p>}
            <div className="flex justify-end">
              <Button
                variant="brand"
                size="sm"
                onClick={handleSend}
                disabled={!body.trim() || sendMessage.isPending}
              >
                {sendMessage.isPending ? "Sending…" : "Send"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
