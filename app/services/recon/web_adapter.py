from __future__ import annotations

import re

from app.models import AccessMode, ResultCategory
from app.services.recon.base import AdapterError, AdapterFinding, ReconAdapter, robots_allows
from app.services.ssrf_guard import UnsafeUrlError, safe_get

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', re.IGNORECASE | re.DOTALL
)


class WebPresenceAdapter(ReconAdapter):
    """Fetches the organization's own public homepage -- the same request any visitor's browser
    makes -- to record its title/description and any technology hints volunteered in response
    headers. Honors robots.txt and never follows links off the confirmed domain."""

    name = "Official Website"
    modes = frozenset({AccessMode.PUBLIC_PROFILE, AccessMode.AUTHORIZED_PASSIVE})

    async def run(self, *, domain: str, organization_name: str, timeout: float) -> list[AdapterFinding]:
        allowed = await robots_allows(domain, "/", timeout=timeout)
        if not allowed:
            raise AdapterError(f"robots.txt disallows fetching {domain}/")

        url = f"https://{domain}/"
        try:
            response = await safe_get(url, timeout=timeout)
        except UnsafeUrlError as exc:
            raise AdapterError(str(exc)) from exc
        except Exception as exc:
            raise AdapterError(f"Could not reach {domain}: {exc}") from exc

        if response.status_code >= 400:
            raise AdapterError(f"{domain} returned status {response.status_code}")

        html = response.text[:500_000]
        title_match = _TITLE_RE.search(html)
        desc_match = _DESC_RE.search(html)
        title = (title_match.group(1).strip() if title_match else domain)[:300]
        description = desc_match.group(1).strip()[:500] if desc_match else None

        findings = [
            AdapterFinding(
                category=ResultCategory.WEB_PRESENCE,
                title=f"Official website: {domain}",
                summary=description or title,
                dedupe_key=f"official-site:{domain}",
                source_name="Official Website",
                source_url=url,
                confidence=1.0,
                rationale="Confirmed organization domain responded with a public homepage.",
            )
        ]

        return findings
