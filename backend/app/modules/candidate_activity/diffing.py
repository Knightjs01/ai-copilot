"""Pure diff function over two ShadowProfileSnapshot dicts (see phantom_passport/schemas.py) --
no I/O, no side effects. Compares exactly the fields that snapshot actually carries; deliberately
conservative about what counts as "material" so a rediscovery candidate never shows with noise
(e.g. summary/notice_period wording tweaks are not surfaced -- skills/seniority/experience/
location/career changes are what a recruiter would actually want to know about)."""

from typing import Any


def diff_passport_snapshots(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    changes: list[str] = []

    old_skills = {str(s).strip().lower() for s in old.get("skills", [])}
    new_skills_raw = list(new.get("skills", []))
    added_skills = [s for s in new_skills_raw if str(s).strip().lower() not in old_skills]
    if added_skills:
        changes.append(f"Added skills: {', '.join(added_skills)}")

    old_seniority = old.get("seniority")
    new_seniority = new.get("seniority")
    if new_seniority and old_seniority != new_seniority:
        changes.append(f"Seniority: {old_seniority or 'Unspecified'} → {new_seniority}")

    old_years = old.get("years_experience")
    new_years = new.get("years_experience")
    if new_years is not None and (old_years is None or new_years > old_years):
        changes.append(f"Experience: {old_years if old_years is not None else '—'} → {new_years} years")

    old_location = old.get("location")
    new_location = new.get("location")
    if new_location and old_location != new_location:
        changes.append(f"Location: {old_location or 'Unspecified'} → {new_location}")

    old_entries = old.get("career_entries", [])
    new_entries = new.get("career_entries", [])
    if len(new_entries) > len(old_entries) and new_entries:
        latest = new_entries[0]
        title = latest.get("title", "a new role")
        changes.append(f"New role added: {title}")

    return changes
