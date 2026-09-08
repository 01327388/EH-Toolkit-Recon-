from __future__ import annotations

from app.models import AccessMode, ResultCategory
from app.services.recon.base import AdapterError, AdapterFinding, ReconAdapter, robots_allows
from app.services.ssrf_guard import UnsafeUrlError, safe_get

_TECH_HEADERS = ["server", "x-powered-by", "x-generator", "via"]


class TechSignalsAdapter(ReconAdapter):
    """Authorized-mode-only: records non-invasive technology signals the target's own homepage
    response headers volunteer (e.g. `Server`, `X-Powered-By`). A single ordinary GET request --
    no probing, fingerprinting payloads, or additional paths."""

    name = "Technology Signals"
    modes = frozenset({AccessMode.AUTHORIZED_PASSIVE})

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

        signals = [
            f"{header}: {response.headers[header]}"
            for header in _TECH_HEADERS
            if header in response.headers
        ]
        if not signals:
            return []

        return [
            AdapterFinding(
                category=ResultCategory.WEB_PRESENCE,
                title=f"Technology signals for {domain}",
                summary="\n".join(signals),
                dedupe_key=f"tech-signals:{domain}",
                source_name="Technology Signals",
                source_url=url,
                confidence=0.6,
                rationale="Values volunteered by the site's own HTTP response headers.",
            )
        ]
