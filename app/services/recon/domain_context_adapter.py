from __future__ import annotations

from app.models import AccessMode, ResultCategory
from app.services.recon.base import AdapterFinding, ReconAdapter


class DomainContextAdapter(ReconAdapter):
    """Records only the confirmed primary domain itself -- no subdomain enumeration -- to satisfy
    Public Profile mode's 'broad domain context' boundary (PROGRAM_REQUIREMENTS.md 6.1)."""

    name = "Confirmed Domain"
    modes = frozenset({AccessMode.PUBLIC_PROFILE})

    async def run(self, *, domain: str, organization_name: str, timeout: float) -> list[AdapterFinding]:
        return [
            AdapterFinding(
                category=ResultCategory.DOMAINS,
                title=domain,
                summary="Confirmed primary domain. Public Profile mode does not enumerate subdomains.",
                dedupe_key=f"primary-domain:{domain}",
                source_name="Confirmed Domain",
                source_url=f"https://{domain}/",
                confidence=1.0,
                rationale="Domain selected during organization confirmation.",
            )
        ]
