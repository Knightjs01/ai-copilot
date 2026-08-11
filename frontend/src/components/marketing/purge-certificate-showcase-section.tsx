import { PurgeCertificateMockup } from "@/components/marketing/mockups/purge-certificate-mockup";

export function PurgeCertificateShowcaseSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            The Burn · Live now
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Close the role. Burn the project. Get an audit certificate.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            One click permanently destroys every resume, sanitized CV, AI note and identity tied
            to a project, then produces a certificate proving exactly what was destroyed and
            when, without a single re-identifiable detail in it.
          </p>
        </div>

        <PurgeCertificateMockup />
      </div>
    </section>
  );
}
