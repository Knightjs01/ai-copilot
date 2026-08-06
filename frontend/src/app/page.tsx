"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { MarketingHome } from "@/components/marketing/marketing-home";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";

export default function HomePage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (isLoading || !user) return;
    router.replace("/projects");
  }, [isLoading, user, router]);

  if (isLoading || user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </main>
    );
  }

  return <MarketingHome />;
}
