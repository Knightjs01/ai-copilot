# Stage 6 of the hiring workflow: Candidate Intelligence Pack — the first module that actually
# calls an LLM (Claude). Scoped to a structured, objective summary only (skills, experience,
# education, narrative) — no scoring, fit rating, or hiring recommendation. This module must
# only ever be given the Phase 4 SanitizedProfile.redacted_text, never a raw resume or any PII
# field on the Candidate record — see app/modules/intelligence/service.py.
