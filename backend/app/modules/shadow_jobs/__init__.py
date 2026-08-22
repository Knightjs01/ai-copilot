"""Shadow: the anonymous job board. Two audiences share this module:

- Companies post/manage ShadowJob listings and review applicants, always through the
  RLS-enforced app_runtime connection (get_tenant_db) — identical tenant isolation to every
  other company-owned resource in this codebase.
- Candidates browse the public board and apply with their Phantom Passport through the
  app_auth connection (get_db), same as every other candidate_auth/phantom_passport route.
  ShadowJob and ShadowApplication both carry company_id and an RLS policy for the company
  side, but app_auth is BYPASSRLS — candidate-facing queries in this module never rely on
  that policy for correctness, they filter explicitly by candidate_user_id from the JWT.

The applicant-facing "Shadow Profile" returned to a company (see schemas.ShadowProfile) is
built by reusing phantom_passport's PhantomPassportRepository and PassportCareerEntryRepository
directly — this module never imports PassportPersonalInfoRepository or PassportPersonalInfo at
all, so it is structurally incapable of leaking a candidate's legal name, phone, or address into
a recruiter-facing response, the same schema-level guarantee phantom_passport itself relies on.

The Reveal Request workflow has since shipped (see shadow_reveal/) and drives ShadowApplication's
status through reveal_requested -> revealed/declined for real. Hiring-pipeline progress
(new/screening/interviewing/offer/hired/rejected) is a separate, independent field --
pipeline_stage -- since ShadowApplicationStatus is entirely about identity-disclosure state, not
where an applicant sits in the hiring process. Still deferred, not built here: AI matching/
ranking, recruiter AI copilot, and Employer Protection blocklists.
"""
