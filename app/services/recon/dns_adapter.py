from __future__ import annotations

import asyncio

import dns.exception
import dns.resolver

from app.models import AccessMode, ResultCategory
from app.services.recon.base import AdapterError, AdapterFinding, ReconAdapter

_RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT"]


class DnsAdapter(ReconAdapter):
    """Queries public DNS resolvers for standard record types. Passive: this only talks to
    recursive DNS resolvers, never to the target's own infrastructure directly."""

    name = "Public DNS"
    modes = frozenset({AccessMode.AUTHORIZED_PASSIVE})

    async def run(self, *, domain: str, organization_name: str, timeout: float) -> list[AdapterFinding]:
        findings: list[AdapterFinding] = []
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout

        loop = asyncio.get_running_loop()
        any_success = False
        for rtype in _RECORD_TYPES:
            try:
                answer = await loop.run_in_executor(None, self._query, resolver, domain, rtype)
            except dns.resolver.NoAnswer:
                any_success = True
                continue
            except dns.resolver.NXDOMAIN as exc:
                raise AdapterError(f"Domain does not resolve: {domain}") from exc
            except dns.exception.Timeout:
                continue
            except Exception:
                continue

            any_success = True
            values = sorted({rdata.to_text().strip().rstrip(".") for rdata in answer})
            if not values:
                continue
            findings.append(
                AdapterFinding(
                    category=ResultCategory.DNS_NETWORK,
                    title=f"{rtype} records for {domain}",
                    summary="\n".join(values),
                    dedupe_key=f"dns:{domain}:{rtype}",
                    source_name="Public DNS",
                    source_url=None,
                    confidence=1.0,
                    rationale=f"Resolved via recursive DNS lookup ({rtype}).",
                )
            )

        if not any_success:
            raise AdapterError(f"DNS lookups failed for {domain}")
        return findings

    @staticmethod
    def _query(resolver: dns.resolver.Resolver, domain: str, rtype: str):
        return resolver.resolve(domain, rtype)
