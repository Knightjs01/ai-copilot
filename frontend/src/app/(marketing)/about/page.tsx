import type { Metadata } from "next";

import { AboutBeliefsSection } from "@/components/marketing/about-beliefs-section";
import { AboutBuiltBySection } from "@/components/marketing/about-built-by-section";
import { AboutFinalCtaSection } from "@/components/marketing/about-final-cta-section";
import { AboutHeroSection } from "@/components/marketing/about-hero-section";

export const metadata: Metadata = {
  title: "About | Phantom Hire",
  description:
    "Identity stays with the candidate until they choose to reveal it. AI shows its evidence, not a verdict. Data that isn't needed doesn't get kept.",
};

export default function AboutPage() {
  return (
    <>
      <AboutHeroSection />
      <AboutBeliefsSection />
      <AboutBuiltBySection />
      <AboutFinalCtaSection />
    </>
  );
}
