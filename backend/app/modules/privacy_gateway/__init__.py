# Stage 5 of the hiring workflow: extract resume text, strip PII, store the sanitized text,
# delete the original file. Deliberately NO LLM call here — CLAUDE.md requires raw CVs never
# reach an AI, so redaction is rule-based (regex + known-name matching), not AI-based. This
# module does NOT produce AI-quality structured data (skills lists, experience timelines) —
# that needs a real LLM or NLP pipeline and belongs to Stage 6 (Candidate Intelligence Pack),
# a separate future phase. What this produces — redacted plain text — is exactly what that
# phase will consume.
