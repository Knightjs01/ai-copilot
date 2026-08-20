"use client";

import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { MessageSquare } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useMyMessageThreads } from "@/lib/queries/messages";

export default function MessagesInboxPage() {
  const { data: threads, isLoading } = useMyMessageThreads();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Messages</h1>
        <p className="text-sm text-muted-foreground">Conversations tied to your applications.</p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && threads?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
            <MessageSquare className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              No conversations yet. A company can message you once you&apos;ve applied.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col gap-3">
        {threads?.map((thread) => (
          <Link key={thread.application_id} href={`/shadow/messages/${thread.application_id}`}>
            <Card className="transition-colors hover:border-muted-foreground/40">
              <CardContent className="flex items-start justify-between gap-4 py-5">
                <div className="flex flex-1 flex-col gap-0.5">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-foreground">{thread.job_title}</h3>
                    {thread.unread_count > 0 && <Badge variant="info">{thread.unread_count}</Badge>}
                  </div>
                  <p className="text-sm text-muted-foreground">{thread.company_name}</p>
                  {thread.last_message_preview && (
                    <p className="line-clamp-1 text-sm text-muted-foreground">
                      {thread.last_message_preview}
                    </p>
                  )}
                </div>
                {thread.last_message_at && (
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {formatDistanceToNow(new Date(thread.last_message_at), { addSuffix: true })}
                  </span>
                )}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
