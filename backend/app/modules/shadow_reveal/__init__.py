"""The Reveal Request workflow: the only place in the Shadow marketplace where a candidate's
real identity crosses from the candidate side to the company side, and it never happens without
the candidate's own explicit approval — unlike app.modules.identity_vault, where a candidate was
added directly to a company's pipeline and never applied anonymously in the first place, so
there is no consent step to gate.

Deliberately a separate module from shadow_jobs, not a few extra methods bolted onto
ShadowJobService: shadow_jobs/__init__.py documents that ShadowJobService is structurally
incapable of reading a candidate's PII because it never imports PassportPersonalInfoRepository.
ShadowRevealService is the one place that import is allowed, and only after checking a
ShadowRevealRequest row is in APPROVED status — keeping the "can this code leak PII" question
answerable by which module you're looking at, not by tracing every call site.

One request per application (unique constraint in migration 0018) — deliberately no re-request
after a decline in this slice; a candidate's "no" is final until a future re-request flow is
built. Reveal here is a snapshot, not a live join: it copies decrypted fields into a response at
approval time, matching the disclosure boundary the product spec calls "minimum necessary" —
legal name, email, phone, and each career entry's real (unmasked) company name. Passport address
is deliberately never included; a hiring reveal doesn't need it.
"""
