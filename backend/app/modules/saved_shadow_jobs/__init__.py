"""Saved Jobs: a candidate's private bookmarks on the Shadow job board.

Purely candidate-owned data — no company_id column, no RLS (same reasoning as
phantom_passports, see migration 0016's docstring). Every route runs on the app_auth
connection (get_db) and filters explicitly by candidate_user_id from the JWT.

`collection_name` is a free-text label (e.g. "Dream roles", "Remote") rather than a
separate Collections model — one flat table stays sufficient for what's actually a small
per-candidate bookmark list.
"""
