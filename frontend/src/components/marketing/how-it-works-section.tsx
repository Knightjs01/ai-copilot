const STEPS = [
  {
    number: "01",
    title: "Open a role",
    body: "Phantom reads the job description, builds an AI Hiring Blueprint, and aligns you with the hiring manager on what actually matters.",
  },
  {
    number: "02",
    title: "Add candidates",
    body: "Each candidate is issued a Callsign the moment they're added. Their CV is sanitized and vault-encrypted automatically, no manual redaction required.",
  },
  {
    number: "03",
    title: "Screen with AI",
    body: "Candidate Intelligence, fit ratings, pre-screen assessments and hand-off notes for the hiring manager, generated without a single real name in sight.",
  },
  {
    number: "04",
    title: "Close the loop",
    body: "Make your hire, then burn the project. Every resume, identity and record goes with Phantom. Only the critical, non-identifying facts stay behind in the Historic Vault.",
  },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="border-t border-border bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-20 lg:py-28">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            How it works
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            One platform, from first job description to the moment the project no longer exists.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step) => (
            <div key={step.number} className="flex flex-col gap-3">
              <span className="text-sm font-semibold text-brand">{step.number}</span>
              <h3 className="text-lg font-semibold text-foreground">{step.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{step.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
