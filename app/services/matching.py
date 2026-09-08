"""Company-name -> organization/domain candidate matching for the search-and-confirm workflow
(PROGRAM_REQUIREMENTS.md 8.1). Uses only keyless, ToS-friendly public APIs: the MediaWiki
opensearch endpoint (built for exactly this kind of programmatic lookup) for name resolution,
and plain DNS resolution to check whether a guessed domain actually exists. No scraping of a
general-purpose search engine, and no active interaction with any candidate organization."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

import dns.exception
import dns.resolver
import httpx

_SUFFIX_RE = re.compile(
    r"\b(inc|incorporated|corp|corporation|co|company|ltd|limited|llc|plc|group|holdings)\b\.?",
    re.IGNORECASE,
)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_TLDS = [".com", ".org", ".io", ".net"]


@dataclass(frozen=True)
class MatchCandidate:
    name: str
    domain: str | None
    confidence: float
    rationale: str
    source: str


def _slugify(name: str) -> str:
    cleaned = _SUFFIX_RE.sub("", name).strip()
    return _NON_ALNUM_RE.sub("", cleaned.lower())


def _word_overlap(a: str, b: str) -> float:
    wa = {w for w in re.split(r"\W+", a.lower()) if w}
    wb = {w for w in re.split(r"\W+", b.lower()) if w}
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _domain_resolves(domain: str) -> bool:
    try:
        dns.resolver.resolve(domain, "A", lifetime=3.0)
        return True
    except dns.exception.DNSException:
        return False
    except Exception:
        return False


async def _first_resolving_domain(slug: str) -> str | None:
    loop = asyncio.get_running_loop()
    for tld in _TLDS:
        candidate = f"{slug}{tld}"
        resolves = await loop.run_in_executor(None, _domain_resolves, candidate)
        if resolves:
            return candidate
    return None


async def _wikipedia_titles(query: str, timeout: float) -> list[str]:
    url = "https://en.wikipedia.org/w/api.php"
    params = {"action": "opensearch", "search": query, "limit": "5", "format": "json"}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params, headers={"User-Agent": "EthicalHawkRecon/0.2"})
        response.raise_for_status()
        data = response.json()
        return data[1] if len(data) > 1 else []
    except Exception:
        return []


async def find_candidates(query: str, *, timeout: float = 6.0, limit: int = 5) -> list[MatchCandidate]:
    candidates: dict[str, MatchCandidate] = {}

    titles = await _wikipedia_titles(query, timeout)
    for title in titles:
        slug = _slugify(title)
        if not slug:
            continue
        domain = await _first_resolving_domain(slug)
        overlap = _word_overlap(query, title)
        confidence = min(0.95, 0.45 + overlap * 0.35 + (0.2 if domain else 0.0))
        rationale = f"Matched public reference \"{title}\""
        rationale += f"; domain {domain} resolves publicly." if domain else "; no matching domain could be confirmed."
        key = domain or f"wiki:{title}"
        candidates[key] = MatchCandidate(
            name=title, domain=domain, confidence=round(confidence, 2), rationale=rationale, source="Wikipedia"
        )

    raw_slug = _slugify(query)
    if raw_slug:
        domain = await _first_resolving_domain(raw_slug)
        if domain and domain not in candidates:
            candidates[domain] = MatchCandidate(
                name=query.strip(),
                domain=domain,
                confidence=0.5,
                rationale=f"Domain {domain} resolves publicly and matches the search text directly.",
                source="DNS heuristic",
            )

    ranked = sorted(candidates.values(), key=lambda c: c.confidence, reverse=True)
    return ranked[:limit]
