from __future__ import annotations

import httpx

from app.models import AccessMode, ResultCategory
from app.services.recon.base import AdapterError, AdapterFinding, ReconAdapter


class RdapAdapter(ReconAdapter):
    """Domain registration context via RDAP (the structured, IANA-standardized successor to WHOIS).
    rdap.org bootstraps to the correct registry -- no scraping, no auth, no ToS-restricted access."""

    name = "Domain Registration (RDAP)"
    modes = frozenset({AccessMode.AUTHORIZED_PASSIVE})

    async def run(self, *, domain: str, organization_name: str, timeout: float) -> list[AdapterFinding]:
        url = f"https://rdap.org/domain/{domain}"
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers={"User-Agent": "EthicalHawkRecon/0.2"})
        except httpx.HTTPError as exc:
            raise AdapterError(f"RDAP request failed: {exc}") from exc

        if response.status_code == 404:
            raise AdapterError(f"No RDAP registration record for {domain}")
        if response.status_code != 200:
            raise AdapterError(f"RDAP returned status {response.status_code}")

        try:
            data = response.json()
        except ValueError as exc:
            raise AdapterError("RDAP returned an unparsable response") from exc

        findings: list[AdapterFinding] = []

        registrar = None
        for entity in data.get("entities", []):
            if "registrar" in (entity.get("roles") or []):
                vcard = entity.get("vcardArray")
                if vcard and len(vcard) > 1:
                    for field in vcard[1]:
                        if field[0] == "fn":
                            registrar = field[3]
                            break
                break

        events = {e.get("eventAction"): e.get("eventDate") for e in data.get("events", [])}
        nameservers = sorted(
            {ns.get("ldhName", "").rstrip(".") for ns in data.get("nameservers", []) if ns.get("ldhName")}
        )

        details = []
        if registrar:
            details.append(f"Registrar: {registrar}")
        if events.get("registration"):
            details.append(f"Registered: {events['registration'][:10]}")
        if events.get("last changed"):
            details.append(f"Last changed: {events['last changed'][:10]}")
        if events.get("expiration"):
            details.append(f"Expires: {events['expiration'][:10]}")
        if nameservers:
            details.append("Nameservers: " + ", ".join(nameservers))

        if details:
            findings.append(
                AdapterFinding(
                    category=ResultCategory.DNS_NETWORK,
                    title=f"Registration record for {domain}",
                    summary="\n".join(details),
                    dedupe_key=f"rdap:{domain}",
                    source_name="Domain Registration (RDAP)",
                    source_url=url,
                    confidence=1.0,
                    rationale="Structured RDAP registration data from the domain's registry/registrar.",
                )
            )
        return findings
