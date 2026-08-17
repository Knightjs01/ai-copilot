// Decorative targeting-reticle corners — used sparingly, on the single hero-tier mockup per
// page, to signal "this is the flagship visual." Purely cosmetic, no semantic meaning. Parent
// must be `relative`.
export function CornerMarks() {
  return (
    <div className="pointer-events-none absolute -inset-3 z-0 hidden sm:block" aria-hidden>
      <span className="absolute left-0 top-0 h-4 w-4 border-l-2 border-t-2 border-brand/50" />
      <span className="absolute right-0 top-0 h-4 w-4 border-r-2 border-t-2 border-brand/50" />
      <span className="absolute bottom-0 left-0 h-4 w-4 border-b-2 border-l-2 border-brand/50" />
      <span className="absolute bottom-0 right-0 h-4 w-4 border-b-2 border-r-2 border-brand/50" />
    </div>
  );
}
