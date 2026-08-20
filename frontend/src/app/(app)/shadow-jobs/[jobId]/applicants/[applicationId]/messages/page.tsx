"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, ShieldAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/lib/auth-context";
import { useApplicantMessages, useMyShadowJob, useSendCompanyMessage } from "@/lib/queries/shadow-jobs";
import { useToast } from "@/lib/toast-context";
import { cn } from "@/lib/utils";

export default function ApplicantMessagesPage() {
  const params = useParams<{ jobId: string; applicationId: string }>();
  const { hasPermission } = useAuth();
  const canView = hasPermission("messages.view");
  const canSend = hasPermission("messages.send");
  const { data: job } = useMyShadowJob(params.jobId);
  const { data: thread, isLoading } = useApplicantMessages(params.jobId, params.applicationId);
  const sendMessage = useSendCompanyMessage(params.jobId, params.applicationId);
  const toast = useToast();
  const [body, setBody] = React.useState("");

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Messages isn&apos;t available on your role</p>
      </div>
    );
  }

  const callsign = thread?.messages.find((m) => m.sender_type === "candidate")?.sender_label;

  const handleSend = () => {
    const trimmed = body.trim();
    if (!trimmed) return;
    sendMessage.mutate(trimmed, {
      onSuccess: () => {
        setBody("");
        toast({ title: "Message sent", variant: "success" });
      },
      onError: () => {
        toast({ title: "Couldn't send message", variant: "danger" });
      },
    });
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link
          href={`/shadow-jobs/${params.jobId}`}
          className="mb-3 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to job
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Messages{callsign ? ` with ${callsign}` : ""}
        </h1>
        {job && <p className="text-sm text-muted-foreground">{job.title}</p>}
      </div>

      <Card>
        <CardContent className="flex flex-col gap-4 py-5">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner className="h-6 w-6 text-muted-foreground" />
            </div>
          ) : thread && thread.messages.length > 0 ? (
            <div className="flex flex-col gap-3">
              {thread.messages.map((message) => (
                <div
                  key={message.id}
                  className={cn("flex flex-col gap-1", message.is_mine ? "items-end" : "items-start")}
                >
                  <span className="text-xs text-muted-foreground">{message.sender_label}</span>
                  <div
                    className={cn(
                      "max-w-[75%] rounded-2xl px-4 py-2.5 text-sm",
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
                {canSend
                  ? "Send the first message to this applicant."
                  : "Nothing here yet — check back once a conversation starts."}
              </p>
            </div>
          )}

          {canSend && (
            <div className="flex flex-col gap-2 border-t border-border pt-4">
              <Textarea
                placeholder="Write a message…"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                disabled={sendMessage.isPending}
              />
              <div className="flex justify-end">
                <Button size="sm" onClick={handleSend} disabled={!body.trim() || sendMessage.isPending}>
                  {sendMessage.isPending ? "Sending…" : "Send"}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
