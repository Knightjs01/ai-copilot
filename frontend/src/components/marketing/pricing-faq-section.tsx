"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const FAQS: { question: string; answer: string }[] = [
  {
    question: "Is Phantom Passport really free?",
    answer:
      "Yes. Creating and using a Phantom Passport, including AI job matching, Shadow applications and verification, costs candidates nothing, forever.",
  },
  {
    question: "Do candidates ever have to pay?",
    answer:
      "No. Phantom's commercial model is built entirely around companies paying for hiring infrastructure, AI, talent intelligence, verification and security. Candidates are the supply side of the marketplace and are never charged.",
  },
  {
    question: "What's the difference between Bronze, Silver, Gold and Platinum?",
    answer:
      "They're candidate verification levels, not subscription tiers. Bronze is a self-declared professional profile. Silver adds identity and employment verification. Gold adds enhanced background and right-to-work checks. Platinum adds high-assurance checks for regulated or security-sensitive roles. All four are free.",
  },
  {
    question: "Do verification levels affect candidate ranking?",
    answer:
      "No. Verification is a trust signal, not a ranking boost. Matching primarily considers skills, experience, role requirements, candidate preferences, career fit and availability. A well-matched Bronze candidate can outrank an irrelevant Platinum candidate.",
  },
  {
    question: "How does Phantom make money?",
    answer:
      "Companies pay through tiered SaaS plans (Free, Pro, Scale, Enterprise), metered AI compute, or an optional success-fee marketplace model where you only pay when you make a hire.",
  },
  {
    question: "What happens when a hiring project closes?",
    answer:
      "You can permanently remove project-specific recruitment data, according to your organisation's configured retention policy, while permitted talent intelligence can be preserved separately in Talent Memory.",
  },
  {
    question: "What does \"Make This Project Disappear\" actually delete?",
    answer:
      "Project-specific data: uploaded CVs, interview notes, transcripts, AI context and personal information tied to that project. It does not retroactively delete Talent Memory records that were separately preserved under your retention policy.",
  },
  {
    question: "Can companies still rediscover candidates after a project is purged?",
    answer:
      "Where your organisation's retention policy permits it, yes, through Talent Memory: skills, experience and match profile, without the original project data or an exposed identity.",
  },
  {
    question: "Can recruiters see a candidate's identity?",
    answer:
      "Not by default. Candidates engage under a Callsign until they choose to reveal appropriate information through a Reveal Request.",
  },
  {
    question: "How does the Reveal Request work?",
    answer:
      "A recruiter requests specific information from a candidate. The candidate decides whether, and how much, to reveal. Nothing is exposed automatically.",
  },
  {
    question: "Are AI credits required to use Phantom?",
    answer:
      "No. Core ATS usage, candidates, applications and pipeline movement, is generous and not metered. AI credits meter compute-intensive features like deep screening, interview summaries and Talent Memory matching.",
  },
  {
    question: "Can I use Phantom as an ATS without using Shadow?",
    answer: "Yes. Phantom ATS, Shadow and Phantom AI can be used independently or together.",
  },
  {
    question: "Can I use Phantom's marketplace without subscribing?",
    answer:
      "Yes. The Phantom Marketplace success-fee model requires no upfront subscription, you pay only when you make a successful hire through the marketplace.",
  },
  {
    question: "Does Phantom automatically make us GDPR compliant?",
    answer:
      "No platform can make an organisation automatically compliant simply by using it. Phantom provides privacy, retention and access-control features designed to support responsible data handling. Organisations remain responsible for configuring and operating the platform appropriately and obtaining appropriate legal advice.",
  },
];

export function PricingFaqSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-3xl px-6 py-16 lg:py-20">
        <div className="text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Frequently asked questions
          </h2>
        </div>

        <Accordion type="single" collapsible className="mt-10">
          {FAQS.map((faq, i) => (
            <AccordionItem key={faq.question} value={`faq-${i}`}>
              <AccordionTrigger>{faq.question}</AccordionTrigger>
              <AccordionContent>{faq.answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
