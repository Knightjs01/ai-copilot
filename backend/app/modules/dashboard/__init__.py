# Company-wide "how's my pipeline doing" rollup for the projects home page — read-only, no
# models of its own. Aggregates across projects/candidates/prescreen_assessment/
# hiring_manager_alignment, all already scoped to the caller's company via RLS + explicit
# company_id filters in each underlying repository.
