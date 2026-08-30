"""Request Introduction -- the third, distinct candidate<->company consent mechanism in this
product (alongside Reveal Request and Talent Pool). A recruiter finds an anonymous candidate via
search and asks whether they're open to a conversation about a specific role; the candidate
accepts or declines without their identity ever being disclosed by this action.

Not a duplicate of either existing mechanism:
- Reveal Request (app.modules.shadow_reveal) is *identity disclosure*, hard-scoped to one
  existing ShadowApplication -- it has nothing to say about a candidate found via search with no
  application yet.
- Talent Pool (app.modules.talent_pool) is *future-role consent* ("keep my profile on file") --
  granting it never opens a conversation and never touches ShadowApplication/Messages at all.

Accepting an introduction auto-creates a real ShadowApplication (see
ShadowJobService.create_application_from_introduction) -- this is deliberate reuse, not a
workaround: it means the existing Messages system (thread-per-application) and Phase 1's
RelationshipStatus computation both start working immediately with zero changes to either.
"""
