# Threat model (MVP)

Lightweight STRIDE-style pass over the main risks for this build.

## Assets

- User credentials and sessions
- Audit log integrity (authentication, authorization acknowledgements, admin actions)
- Recon result data (source-attributed, potentially sensitive in aggregate)
- Availability of the app and of the internal network it runs on (SSRF risk)
- Third-party sources' own availability/ToS (we are a client of crt.sh, RDAP, Wikipedia, and
  target organizations' own web servers)

## Key risks and mitigations

| Risk | Mitigation |
| --- | --- |
| SSRF via a malicious "domain" during org confirmation, reaching internal services (metadata endpoints, internal admin panels) | `app/services/ssrf_guard.py`: resolves and validates every hostname against private/loopback/link-local/reserved ranges before connecting; re-validates every redirect hop (redirects are not auto-followed by the HTTP client); response size cap. |
| CSRF on state-changing forms (register, login, run creation, hide-result, notes, admin actions) | Double-submit cookie pattern: a `csrf_token` cookie is set on every GET and compared to a hidden form field via constant-time comparison on every POST (`app/deps.py::verify_csrf`). |
| Session fixation / tampering | Sessions are a signed (`itsdangerous`), time-limited token in an `httponly`, `samesite=lax` cookie — not a raw user id, and not readable/forgeable client-side. |
| Credential stuffing / weak passwords | Argon2 hashing; minimum 10-character password enforced server-side; failed logins are audit-logged (without the attempted password). |
| Unbounded background work / resource exhaustion from recon jobs | Bounded worker pool (`MAX_CONCURRENT_JOBS`), bounded per-run adapter concurrency, per-adapter timeout, per-user hourly run rate limit, and a `RECON_KILL_SWITCH` to halt all recon centrally. |
| A single flaky/blocked source taking down an entire run | Every adapter call is isolated (`AdapterError` + `asyncio.gather`); failures degrade the run to "incomplete source coverage" instead of failing or crashing the worker. |
| Privilege escalation (member acting as administrator) | Role stored server-side on `User`, checked via `require_admin` dependency on every `/admin/*` route; an administrator cannot demote or deactivate themselves through the UI, preventing accidental lockout. |
| Leaking internals in error responses | A catch-all exception handler renders a generic message and logs the real exception server-side only; validation errors shown to users are the specific, safe Pydantic messages we authored, not stack traces. |
| Over-collection / privacy risk from aggregating public data | Category boundaries are enforced in code, not just UI copy: Public Profile mode only runs adapters whose `modes` includes `PUBLIC_PROFILE` (domain confirmation, homepage title, Wikipedia summary); subdomain enumeration, DNS record dumps, and the best-effort People extraction only run in Authorized Passive Recon mode, which requires a recorded acknowledgement first. |
| Unauthorized/unaccountable use of Authorized Passive Recon | `AuthorizationAcknowledgement` is a required row (user, organization, purpose, timestamp) before that mode's adapters run, and an `AuditEvent` is written alongside it. |
| Analyst hides a result to suppress accurate findings from others | Hiding is scoped to the run/workspace and requires a reason that is itself audit-logged (`result.hidden` event) — it does not delete the underlying `ReconResult` row. |

## Explicit non-goals (by design, not oversight)

- No active scanning, exploitation, credential testing, or authentication to target systems —
  enforced by which adapters exist at all, not by a runtime toggle.
- No document upload in this MVP (PROGRAM_REQUIREMENTS.md 8.4) — the attack surface of untrusted
  file parsing/storage/malware scanning is deliberately deferred.
- No multi-tenant data isolation beyond per-user run ownership; there is no organization/team
  concept yet, so this is not intended for multi-customer deployment as-is.

## Known gaps for a real deployment

- Password reset currently displays the link in-app (no email service configured) — must be
  replaced before any non-local use.
- No dependency/secret scanning wired into CI yet beyond `ruff`; add `pip-audit`/`safety` and a
  secret scanner before a public launch, per PROGRAM_REQUIREMENTS.md 10.3.
- TLS termination, secure cookie flags (`secure=True`), and HSTS are not configured here — this
  app assumes it sits behind a reverse proxy/hosting platform that terminates HTTPS for anything
  beyond local development.
