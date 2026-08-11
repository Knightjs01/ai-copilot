# The Phantom Passport — a candidate's reusable, self-owned professional identity, and the
# schema-level split between what's discoverable and what's protected.
#
# PhantomPassport (this module) = the Shadow Profile: headline, skills, career history,
# preferences — everything a recruiter or the AI matching engine is allowed to see. It has no
# name, email, phone, or address column. That's deliberate: the split between professional and
# personal data isn't a display filter applied to one shared record (the way an earlier version
# of this app hid PII on the same Candidate row) — it's two separate tables, and code that only
# has a PhantomPassport in scope has no way to accidentally leak a name, because there's no name
# column to leak.
#
# PassportPersonalInfo = the candidate's own master copy of their real identity, Fernet-encrypted
# with the same key as identity_vault. It is never read by any Shadow Profile, matching, search,
# or recruiter-facing code path. Once the Shadow job board / apply flow exists, applying to a
# project will copy (still encrypted) from here into that project's own
# identity_vault.CandidateIdentityVault row — the Project Vault referenced throughout the Shadow
# spec — rather than this table ever being queried directly by anything project-scoped.
#
# PassportCareerEntry.company_name_encrypted is the real employer (private); .company_name_anonymized
# is the generalized version ("Global Payments Platform" instead of "Stripe") a Shadow Profile
# would actually display — both live on the same row rather than trying to derive one from the
# other at read time, because generalizing a company name is a judgment call the CV-parsing LLM
# makes once, not something safe to recompute generically later.
#
# Deferred to later phases, deliberately not built here: Employer Protection (blocking specific
# companies/recruiters from seeing this Passport — spec Phase 2), the Shadow job board and
# one-click apply, and any verification badge that would imply a real check happened —
# verification_status defaults to "unverified" and nothing in this codebase ever sets it to
# "verified" yet.
