import type { Metadata } from "next";

import { JobApplicationShowcaseSection } from "@/components/marketing/job-application-showcase-section";
import { JobBoardShowcaseSection } from "@/components/marketing/job-board-showcase-section";
import { JobSeekersCtaSection } from "@/components/marketing/job-seekers-cta-section";
import { JobSeekersHeroSection } from "@/components/marketing/job-seekers-hero-section";
import { JobSeekersPromiseSection } from "@/components/marketing/job-seekers-promise-section";
import { PhantomStorySection } from "@/components/marketing/phantom-story-section";
import { ZeroRetentionSection } from "@/components/marketing/zero-retention-section";

export const metadata: Metadata = {
  title: "For Job Seekers | Phantom Hire",
  description:
    "Explore your next opportunity without announcing you're looking. Anonymous by default, AI-matched, verified when it matters, zero-retention when you're done.",
};

export default function JobSeekersPage() {
  return (
    <>
      <JobSeekersHeroSection />
      <JobSeekersPromiseSection />
      <JobBoardShowcaseSection />
      <JobApplicationShowcaseSection />
      <ZeroRetentionSection />
      <PhantomStorySection />
      <JobSeekersCtaSection />
    </>
  );
}
