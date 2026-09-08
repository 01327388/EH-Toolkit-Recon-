from __future__ import annotations

from app.models import AccessMode, ResultCategory
from app.services.recon.base import AdapterError, AdapterFinding, ReconAdapter, robots_allows
from app.services.ssrf_guard import UnsafeUrlError, safe_get

# Conventional, widely-used public paths. We only ever visit URLs on the organization's own
# confirmed domain -- never a third-party search index -- and only if robots.txt permits it.
_CANDIDATE_PATHS = {
    "/press": "Press/News",
    "/newsroom": "Press/News",
    "/news": "Press/News",
    "/investors": "Investor Relations",
    "/about": "About",
    "/careers": "Careers",
    "/security.txt": "Security Policy",
    "/.well-known/security.txt": "Security Policy",
}


class PublicDocumentsAdapter(ReconAdapter):
    """Checks a small set of conventional public paths on the organization's own domain (press,
    investor relations, security.txt, etc.) rather than scraping any third-party search index --
    keeping this within source ToS and away from access-controlled material."""

    name = "Public Pages"
    modes = frozenset({AccessMode.AUTHORIZED_PASSIVE})

    async def run(self, *, domain: str, organization_name: str, timeout: float) -> list[AdapterFinding]:
        findings: list[AdapterFinding] = []
        reachable = False

        for path, doc_type in _CANDIDATE_PATHS.items():
            if not await robots_allows(domain, path, timeout=timeout):
                continue
            url = f"https://{domain}{path}"
            try:
                response = await safe_get(url, timeout=timeout)
            except UnsafeUrlError:
                continue
            except Exception:
                continue

            reachable = True
            if response.status_code == 200:
                findings.append(
                    AdapterFinding(
                        category=ResultCategory.DOCUMENTS,
                        title=f"{doc_type}: {domain}{path}",
                        summary=f"Publicly accessible {doc_type.lower()} page on the confirmed domain.",
                        dedupe_key=f"public-page:{domain}{path}",
                        source_name="Public Pages",
                        source_url=url,
                        confidence=0.9,
                        rationale="Conventional public path returned HTTP 200 without authentication.",
                    )
                )

        if not reachable:
            raise AdapterError(f"Could not reach any known public paths on {domain}")
        return findings
