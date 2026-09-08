from __future__ import annotations

import json
import re

import httpx

from app.models import AccessMode, ResultCategory
from app.services.recon.base import AdapterError, AdapterFinding, ReconAdapter

_VALID_HOST_RE = re.compile(r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)+$")


class CrtShAdapter(ReconAdapter):
    """Certificate-transparency log search (crt.sh) for subdomains publicly logged via issued
    TLS certificates. A well-established passive-recon technique: it queries a third-party public
    ledger, never the target itself."""

    name = "Certificate Transparency (crt.sh)"
    modes = frozenset({AccessMode.AUTHORIZED_PASSIVE})

    async def run(self, *, domain: str, organization_name: str, timeout: float) -> list[AdapterFinding]:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    url, headers={"User-Agent": "EthicalHawkRecon/0.2 (+passive-research-tool)"}
                )
        except httpx.HTTPError as exc:
            raise AdapterError(f"crt.sh request failed: {exc}") from exc

        if response.status_code != 200:
            raise AdapterError(f"crt.sh returned status {response.status_code}")

        try:
            rows = json.loads(response.text)
        except (json.JSONDecodeError, ValueError) as exc:
            raise AdapterError("crt.sh returned an unparsable response") from exc

        subdomains: set[str] = set()
        for row in rows:
            name_value = row.get("name_value", "")
            for candidate in name_value.split("\n"):
                candidate = candidate.strip().lower().lstrip("*.")
                if candidate and candidate.endswith(domain) and _VALID_HOST_RE.match(candidate):
                    subdomains.add(candidate)

        findings = [
            AdapterFinding(
                category=ResultCategory.DOMAINS,
                title=sub,
                summary=f"Observed in public certificate transparency logs for {domain}.",
                dedupe_key=f"subdomain:{sub}",
                source_name="Certificate Transparency (crt.sh)",
                source_url=f"https://crt.sh/?q={sub}",
                confidence=0.75,
                rationale="Hostname appeared on a publicly issued, publicly logged TLS certificate.",
            )
            for sub in sorted(subdomains)
        ]
        return findings
