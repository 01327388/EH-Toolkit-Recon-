"""Outbound-request safety guard.

Every passive-recon adapter that fetches a URL derived from user/target input
(as opposed to a fixed, trusted API host) must go through `safe_get` here.
It blocks requests to private, loopback, link-local, and other non-public
address space, refuses non-HTTP(S) schemes, and re-validates every redirect
hop so a target can't bounce us to an internal address. See
PROGRAM_REQUIREMENTS.md 10.3.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import httpx

MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 2_000_000
_ALLOWED_SCHEMES = {"http", "https"}


class UnsafeUrlError(Exception):
    pass


def _resolve_all(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"Could not resolve host: {hostname}") from exc
    addrs = []
    for info in infos:
        raw = info[4][0]
        addrs.append(ipaddress.ip_address(raw.split("%")[0]))
    return addrs


def _is_public(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return not (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


def assert_safe_url(url: str) -> str:
    """Validates scheme + resolved address space. Returns the normalized URL or raises UnsafeUrlError."""
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise UnsafeUrlError(f"Unsupported URL scheme: {parsed.scheme!r}")
    if not parsed.hostname:
        raise UnsafeUrlError("URL has no hostname")
    if parsed.hostname.lower() in {"localhost"}:
        raise UnsafeUrlError("Refusing to fetch localhost")

    addrs = _resolve_all(parsed.hostname)
    if not addrs:
        raise UnsafeUrlError(f"No addresses resolved for {parsed.hostname}")
    for addr in addrs:
        if not _is_public(addr):
            raise UnsafeUrlError(f"Refusing to fetch non-public address {addr} for host {parsed.hostname}")
    return url


async def safe_get(
    url: str,
    *,
    timeout: float,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """GETs a URL that may point at target-controlled infrastructure, with SSRF protections.

    Follows redirects manually (bounded) and re-validates each hop before following it.
    Raises UnsafeUrlError if the URL or any redirect target is unsafe.
    """
    current = assert_safe_url(url)
    default_headers = {
        "User-Agent": "EthicalHawkRecon/0.2 (+passive-research-tool; authorized-use-only)"
    }
    if headers:
        default_headers.update(headers)

    async with httpx.AsyncClient(follow_redirects=False, timeout=timeout) as client:
        for _ in range(MAX_REDIRECTS + 1):
            response = await client.get(current, headers=default_headers)
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    return response
                current = assert_safe_url(str(httpx.URL(current).join(location)))
                continue
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                raise UnsafeUrlError("Response exceeds maximum allowed size")
            return response
        raise UnsafeUrlError("Too many redirects")
