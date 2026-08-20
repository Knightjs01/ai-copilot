"""Phantom AI Co-Pilot: a scoped, tool-calling assistant for Shadow candidates, embedded
contextually on the job detail, Passport, Applications, and Interviews pages. Not an open-ended
chatbot -- every Claude call this module makes is a forced tool call, same discipline as every
other AI feature in this codebase. The router step (see llm_client.py::route) is the one genuine
exception to "exactly one tool per call": it gives Claude a CHOICE of tools via
`tool_choice={"type": "any"}`, but Claude still MUST call exactly one of them -- even plain
conversational chit-chat goes through the `reply` tool (a single `message` field), so no branch
of this feature is ever a free-form completion.

Fully stateless: no models, no migration. The frontend holds the conversation transcript in
client state and resends a capped recent-history window each turn.

At most 2 Claude calls per user turn: (1) the router, (2) the picked action's own existing
forced-tool call, if that action is generative. `summarize_applications` is pure retrieval
(zero extra calls) and `reply`'s answer is already the router call's own tool input (zero extra
calls). The final chat reply text is always template-formatted server-side from structured
data -- never a third "chat-ify this" call.

Reuses passport_matching.service.parse_search_query/get_or_compute_match and
phantom_passport.service.suggest_summary_improvement directly rather than reimplementing them.
Deliberately does NOT reuse interview_kit (a different feature: company-side, project-scoped,
grounded in the Hiring Blueprint) for interview-prep questions -- this module's own
generate_interview_prep is candidate-side, ad-hoc, and grounded only in the job's public
requirements/description.
"""
