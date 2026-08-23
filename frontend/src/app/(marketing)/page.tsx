"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { MarketingHome } from "@/components/marketing/marketing-home";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";

function HomePageContent() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  // "Back to Phantom Hire" (app-header.tsx) links here with this param specifically so a
  // logged-in user can actually see the marketing site instead of being bounced straight back
  // into the app -- landing on "/" any other way (a stale bookmark, typing the URL) still
  // redirects a logged-in user into their dashboard, unchanged.
  const wantsMarketingView = searchParams.get("view") === "marketing";

  React.useEffect(() => {
    if (isLoading || !user || wantsMarketingView) return;
    router.replace("/projects");
  }, [isLoading, user, wantsMarketingView, router]);

  if (isLoading || (user && !wantsMarketingView)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return <MarketingHome />;
}

export default function HomePage() {
  return (
    <React.Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      }
    >
      <HomePageContent />
    </React.Suspense>
  );
}
