"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const FAQS: { question: string; answer: string }[] = [
  {
    question: "Is Phantom an ATS?",
    answer:
      "Yes. Phantom Core includes a full applicant tracking system: roles, pipeline, interviews, messaging and team collaboration. Network and Intelligence add private talent discovery and AI on top of that same ATS.",
  },
  {
    question: "What's the difference between Core and Network?",
    answer:
      "Core runs your hiring process. Network adds Shadow, Phantom's anonymous job board, and access to Phantom's verified talent network, so you can discover candidates who aren't applying anywhere publicly, not just manage the ones who already have.",
  },
  {
    question: "Do candidates ever have to pay?",
    answer:
      "No. Creating a Phantom Passport, browsing Shadow and applying to roles is free for candidates, forever. Phantom's commercial model is built entirely around companies paying for hiring infrastructure, talent discovery and intelligence.",
  },
  {
    question: "Can candidates remain anonymous?",
    answer:
      "Yes. Candidates engage under a Callsign until they choose to reveal their identity through a Reveal Request. Nothing is exposed automatically.",
  },
  {
    question: "Can I upgrade later?",
    answer:
      "Yes. You can move between Core, Network and Intelligence as your hiring needs grow, with no long-term lock-in.",
  },
  {
    question: "Is there an Enterprise plan?",
    answer:
      "Yes. Enterprise adds SSO, advanced permissions, custom workflows and dedicated support for larger or more complex organisations. Contact us for pricing.",
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
