"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const FAQS: { question: string; answer: string }[] = [
  {
    question: "What counts as an active role?",
    answer:
      "An active role is a hiring process that's currently live — not a lifetime posting limit. If you close a role, it stops counting immediately and you can open another in its place. A company on Core running 5 active roles that closes one can start a new one straight away, still on Core.",
  },
  {
    question: "What's the difference between Core, Growth and Scale?",
    answer:
      "All three include the full Phantom platform — ATS, Shadow, Candidate Passport and AI-powered hiring. Core supports up to 5 active roles. Growth raises that to 6–10 and adds enhanced employer branding and hiring analytics. Scale is for larger, established talent teams with configurable capacity, advanced permissions and enterprise controls.",
  },
  {
    question: "Do candidates ever have to pay?",
    answer:
      "No. Creating a Phantom Passport, browsing Shadow and applying to roles is free for candidates, forever. Phantom's commercial model is built entirely around companies paying for the platform.",
  },
  {
    question: "Can candidates remain anonymous?",
    answer:
      "Yes. Candidates engage under a Callsign until they choose to reveal their identity through a Reveal Request. Nothing is exposed automatically.",
  },
  {
    question: "Can I upgrade later?",
    answer:
      "Yes. You can move between Core, Growth and Scale as your hiring needs grow, with no long-term lock-in and no disruption to your existing roles or candidates.",
  },
  {
    question: "Is Scale's active-role limit fixed?",
    answer:
      "No. Scale supports 11+ active roles and is configured around your team's actual hiring volume, not a fixed number. Talk to us and we'll set it up for you.",
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
