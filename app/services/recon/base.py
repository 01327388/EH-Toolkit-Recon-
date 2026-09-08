from __future__ import annotations

import urllib.robotparser
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models import AccessMode, ResultCategory
from app.services.ssrf_guard import safe_get

USER_AGENT = "EthicalHawkRecon/0.2 (+passive-research-tool; authorized-use-only)"


class AdapterError(Exception):
    """Raised when a source adapter cannot complete. Caught per-adapter by the pipeline
    so one flaky/blocked source degrades the run to 'incomplete' rather than failing it."""


@dataclass(frozen=True)
class AdapterFinding:
    category: ResultCategory
    title: str
    summary: str | None
    dedupe_key: str
    source_name: str
    source_url: str | None
    confidence: float
    rationale: str | None = None


class ReconAdapter(ABC):
    name: str
    modes: frozenset[AccessMode]

    @abstractmethod
    async def run(self, *, domain: str, organization_name: str, timeout: float) -> list[AdapterFinding]:
        """Return normalized findings. Raise AdapterError on failure; never raise other exceptions."""


async def robots_allows(domain: str, path: str, *, timeout: float) -> bool:
    """Best-effort robots.txt check. Fails open (allows) only if robots.txt itself is unreachable,
    since an unreachable robots.txt is not a disallow signal -- but any parsed rule is honored."""
    try:
        response = await safe_get(f"https://{domain}/robots.txt", timeout=timeout)
    except Exception:
        return True
    if response.status_code >= 400:
        return True
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(response.text.splitlines())
    try:
        return parser.can_fetch(USER_AGENT, path)
    except Exception:
        return True
