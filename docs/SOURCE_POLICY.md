# Source policy

EthicalHawk Recon only collects information through the sources below. Every adapter lives in
`app/services/recon/` and implements the same `ReconAdapter` interface so this list stays accurate.

## Sources used

| Source | How it's accessed | Rate/scope limits |
| --- | --- | --- |
| Public recursive DNS | `dnspython` queries to standard resolvers | One query per record type per run |
| RDAP (`rdap.org`) | Single HTTPS GET per run | Bootstraps to the correct registry; no auth |
| Certificate Transparency (`crt.sh`) | Single HTTPS GET per run | Public CT log search, standard passive-recon technique |
| Wikipedia REST summary + opensearch APIs | HTTPS GET, official MediaWiki API endpoints | Built for programmatic access; no key required |
| The confirmed organization's own domain | HTTPS GET to `/` and a small fixed list of conventional paths (`/press`, `/investors`, `/security.txt`, ...) | robots.txt is checked before every fetch; SSRF-guarded; capped response size |

## What is explicitly not done

- No scraping of general-purpose search engines (Google, Bing, etc.) — those results would be
  outside the source's own API terms for automated collection.
- No crawling beyond the fixed path list above — no following of arbitrary links.
- No professional-network (e.g. LinkedIn) scraping for the People & Organization category. That
  category is populated only from name/title mentions Wikipedia's own editors have already
  publicly attributed, and is explicitly low-confidence and asks the analyst to verify independently.
- No authentication, no bypassing of paywalls/access controls/rate limits.
- No collection of personal contact details, credentials, or financial data.

## Safety controls (see also `docs/THREAT_MODEL.md`)

- `app/services/ssrf_guard.py` blocks requests to private/loopback/link-local/reserved address
  space and re-validates every redirect hop, for the two adapters that fetch a target-controlled
  URL (homepage + conventional paths).
- `app/services/recon/base.py::robots_allows` checks `robots.txt` before every fetch to the
  target's own domain.
- Per-run adapter concurrency, a global concurrent-job cap, a per-user hourly run limit, and a
  `RECON_KILL_SWITCH` environment flag are enforced in `app/services/pipeline.py` / `app/background.py`.
- Every adapter failure is caught individually (`AdapterError`) so one blocked/flaky source
  degrades a run to "incomplete source coverage" rather than failing the whole run or crashing
  the worker.
