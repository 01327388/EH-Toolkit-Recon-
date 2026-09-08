from __future__ import annotations

import httpx

from app.models import AccessMode, ResultCategory
from app.services.recon.base import AdapterError, AdapterFinding, ReconAdapter


class WikipediaOverviewAdapter(ReconAdapter):
    """Public company summary via the Wikipedia REST summary API. Used for the conservative
    Public Profile description, and mirrored into Authorized mode for continuity."""

    name = "Wikipedia"
    modes = frozenset({AccessMode.PUBLIC_PROFILE, AccessMode.AUTHORIZED_PASSIVE})

    async def run(self, *, domain: str, organization_name: str, timeout: float) -> list[AdapterFinding]:
        title = organization_name.strip().replace(" ", "_")
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers={"User-Agent": "EthicalHawkRecon/0.2"})
        except httpx.HTTPError as exc:
            raise AdapterError(f"Wikipedia request failed: {exc}") from exc

        if response.status_code == 404:
            return []
        if response.status_code != 200:
            raise AdapterError(f"Wikipedia returned status {response.status_code}")

        data = response.json()
        if data.get("type") == "disambiguation":
            return []

        extract = (data.get("extract") or "").strip()
        if not extract:
            return []

        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", url)
        return [
            AdapterFinding(
                category=ResultCategory.WEB_PRESENCE,
                title=data.get("title", organization_name),
                summary=extract,
                dedupe_key=f"wiki-summary:{data.get('title', organization_name)}",
                source_name="Wikipedia",
                source_url=page_url,
                confidence=0.7,
                rationale="Public encyclopedia summary matched by organization name.",
            )
        ]
