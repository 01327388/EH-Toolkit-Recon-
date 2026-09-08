"""Saved-run comparison (PROGRAM_REQUIREMENTS.md 8.3). Diffs are presented as plain additions,
removals, and changes -- never labeled as vulnerabilities or risk findings."""

from __future__ import annotations

from dataclasses import dataclass

from app.models import ReconResult


@dataclass(frozen=True)
class ChangeEntry:
    status: str  # "added" | "removed" | "changed"
    category: str
    current: ReconResult | None
    previous: ReconResult | None


def diff_runs(previous_results: list[ReconResult], current_results: list[ReconResult]) -> list[ChangeEntry]:
    previous_by_key = {r.dedupe_key: r for r in previous_results if not r.hidden}
    current_by_key = {r.dedupe_key: r for r in current_results if not r.hidden}

    entries: list[ChangeEntry] = []

    for key, current in current_by_key.items():
        previous = previous_by_key.get(key)
        if previous is None:
            entries.append(ChangeEntry("added", current.category.value, current, None))
        elif previous.summary != current.summary or previous.title != current.title:
            entries.append(ChangeEntry("changed", current.category.value, current, previous))

    for key, previous in previous_by_key.items():
        if key not in current_by_key:
            entries.append(ChangeEntry("removed", previous.category.value, None, previous))

    order = {"added": 0, "changed": 1, "removed": 2}
    entries.sort(key=lambda e: (order[e.status], e.category))
    return entries
