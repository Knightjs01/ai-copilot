"""Read-only aggregation over event data that already exists elsewhere (ShadowApplication,
ShadowRevealRequest, TalentPoolGrant, CandidatePass, IntroductionRequest, Message) -- no models
or migrations of its own, same shape as the `dashboard` module. Three real, bounded surfaces:

1. Interaction timeline -- one candidate's full real history with a company, merged across every
   event source above. Generalizes the existing single-application audit view
   (shadow_jobs.list_applicant_activity, scoped to one shadow_application_id and explicitly
   excluding Talent Pool/Pass events by its own documented scope cut) into the real thing that
   view's own docstring flagged as a future join worth adding.
2. Candidate Rediscovery -- for every candidate this company has passed on, diffs their current
   Passport snapshot against the snapshot that was live at pass time (derived from existing
   PassportVersion rows by timestamp, no new stored reference needed) and surfaces only the ones
   with a real, material change.
3. AI Recommendation -- reuses PassportMatchingService.search_candidates_for_job exactly as-is
   against the company's most recently published job, surfacing only genuinely new (relationship
   status "new") top matches. Not a new AI system -- the same real scoring engine, applied once,
   lazily, never on every dashboard load.
"""
