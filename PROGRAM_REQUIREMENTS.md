# EthicalHawk Recon — Program Requirements Document

**Version:** 0.2 (portfolio MVP)  
**Owner:** Junior Software Developer / Cybersecurity Graduate  
**Status:** Proposed

## 1. Product summary

EthicalHawk Recon is an authorization-aware, passive reconnaissance web application for security professionals. It helps users turn publicly available organizational information into a structured, source-attributed research workspace. A user searches for a company, confirms the intended organization, and receives categorized results covering its public web presence, domains, technology signals, public documents, professional company information, and DNS/network metadata.

The project is intended to demonstrate secure full-stack engineering, responsible cybersecurity judgment, and polished product design to cybersecurity employers while remaining an ongoing career project. It is a reconnaissance and research tool, not a vulnerability scanner or exploitation platform.

## 2. Problem and opportunity

Early-stage security assessments often involve scattered, difficult-to-verify public information. Analysts may need to review an organization's public footprint, identify changes over time, and establish a clear assessment scope before conducting any authorized testing. EthicalHawk Recon organizes that research in one interface, retaining where and when each result was discovered.

## 3. Users

| User | Need |
| --- | --- |
| Junior penetration tester | Build a structured, attributed public-footprint profile before an approved engagement. |
| Application-security analyst | Understand an organization's web-facing asset landscape and changes over time. |
| SOC / blue-team analyst | Investigate public exposure context and retain research history. |
| Portfolio reviewer / employer | See secure design, responsible reconnaissance boundaries, clear data provenance, and thoughtful UI work. |

## 4. Product goals

- Provide a simple search-and-confirm workflow beginning with a company name.
- Organize passive-recon results into clear, navigable categories instead of a long unstructured report.
- Preserve source attribution and discovery time so users can evaluate result credibility.
- Support saved reconnaissance runs and highlight meaningful changes between them.
- Make authorization status, data minimization, auditability, and user trust visible product features.
- Deliver a modern, portfolio-quality interface without performing active testing.

## 5. Scope and safety boundaries

### 5.1 Included in the MVP

- Search and organization-confirmation workflow based on a company name.
- Passive collection and presentation of permitted, publicly available organizational information.
- Source-attributed results, discovery timestamps, saved runs, and change comparison.
- A conservative public-profile mode and a fuller authorized-recon mode.

### 5.2 Explicitly excluded

- Vulnerability scanning, port scanning, exploitation, credential testing, brute force, payload delivery, denial-of-service testing, stealth, or evasion.
- Active probing of target systems, authenticated testing, or automated interaction with target application workflows.
- Collection, enrichment, or display of sensitive personal data, personal contact details, credentials, secrets, financial data, or data behind access controls.
- Bypassing robots controls, authentication, rate limits, paywalls, access controls, or source terms.

## 6. Access modes and authorization

### 6.1 Public Profile mode

No authorization acknowledgement is required for a conservative profile of an organization. Results must remain high-level and limited to low-risk, publicly presented organizational information, such as the official website, public company description, public brand/social links, and broad domain context. The interface must state that Public Profile mode is informational and does not establish permission for testing.

### 6.2 Authorized Passive Recon mode

Before fuller passive recon is available, the user must acknowledge that they are authorized to assess the selected organization. The acknowledgement records the user, target, time, and intended purpose in an audit event. This mode may organize permitted public technical and professional information, but it remains passive and follows the same privacy and source restrictions.

Authorization acknowledgement is a product control, not legal advice or a substitute for contractual permission.

## 7. Core user journey

1. The user signs in and searches by company name.
2. The app presents likely organization and domain matches in a search-engine-style results screen.
3. The user confirms the intended organization and selects Public Profile or, when authorized, Authorized Passive Recon mode.
4. The service gathers allowed passive information and displays progress without contacting the target in an active-testing manner.
5. The user reviews categorized results, each with source and discovery time.
6. The run is saved; later runs show additions, removals, and changes for analyst review.

## 8. Functional requirements

### 8.1 Search, matching, and confirmation

- Begin each research run with a company-name search field.
- Return possible organization/domain matches with enough public context for the user to select the intended target.
- Require explicit target confirmation before collection begins.
- Clearly display the selected organization, scope, access mode, and run status throughout the workflow.
- Prevent ambiguous or malformed requests from automatically initiating a broad search.

### 8.2 Passive-recon result categories

The left-side navigation must provide the following categories:

- **Overview:** organizational summary, result totals, source coverage, run status, and important changes since the previous run.
- **Domains & Subdomains:** confirmed public domains and subdomains, relationship/confidence indication, source, and discovery time.
- **Web Presence:** official websites, public-facing web properties, and non-invasive technology signals observed from permitted public information.
- **People & Organization:** publicly listed professional names, titles, and official company/profile references where permitted. Do not collect or display sensitive personal data or personal contact details.
- **Public Documents:** publicly accessible organization-published documents, titles, URLs, type, and discovery time. Do not bypass access controls or index private material.
- **DNS & Network Context:** public DNS records and high-level infrastructure context, with source, confidence, and discovery time.
- **Changes:** comparison of saved runs, including newly discovered, removed, or materially changed results.

Each result must include its category, source link/name, discovery timestamp, confidence or match rationale where available, and a safe method to report or hide inaccurate data.

### 8.3 Saved runs and change history

- Save completed reconnaissance runs for signed-in users.
- Allow a user to open prior runs and compare a new run with a selected earlier run.
- Identify additions, removals, and material changes without claiming they are vulnerabilities.
- Keep a result history showing when an item was first and last observed.
- Let users add text-only analyst notes to a run or individual result.

### 8.4 Future document ingestion

- Document upload is explicitly out of scope for the MVP.
- A later release may accept documents only when the user confirms they own them or are authorized to provide them.
- Future ingestion must include file-type/size restrictions, malware scanning, encrypted storage, retention/deletion controls, and clear source labeling separating uploaded material from public-source results.

### 8.5 Accounts, audit, and data controls

- Support account registration, sign-in, sign-out, password reset, and role-based access for `member` and `administrator` roles.
- Record audit events for authentication, target confirmation, authorization acknowledgements, run creation, result suppression, and administrative actions.
- Offer users a way to hide inaccurate results from their own workspace and record the reason.
- Do not store passwords, private target credentials, secrets, or unnecessarily complete copies of third-party pages.

## 9. User interface requirements

The interface should be simple, modern, and calm: a sleek cream and white base, orange as the restrained primary accent, dark readable text, spacious cards, and clear dividers. It should look like a focused professional research tool, not a hacker-themed console.

- **App shell:** fixed left-side category navigation on desktop; compact, accessible navigation on mobile.
- **Search landing page:** one prominent company-name search field, a concise explanation of the two access modes, and clear responsible-use language.
- **Organization confirmation:** search-engine-style candidate cards showing company name, likely official domain, and enough context to safely select the intended organization.
- **Research dashboard:** category summary cards, progress state, source coverage, recent results, and a visible mode badge: `Public Profile` or `Authorized Passive Recon`.
- **Category views:** filterable, easy-to-scan result tables/cards; every item exposes its source and discovery time without requiring a deep click-through.
- **Changes view:** plain-language additions, removals, and changes with before/after context and links to relevant sources.
- **Notes:** lightweight text-only notes on individual results and runs.
- **States:** loading, empty, incomplete-source, and error states must explain what occurred without exposing system details.
- Meet WCAG 2.2 AA basics: semantic controls, keyboard navigation, visible focus, adequate contrast, labels, color-independent status indicators, and responsive layouts.

## 10. Technical requirements

### 10.1 Recommended MVP stack

- **Backend:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic.
- **Frontend:** server-rendered Jinja templates plus HTMX, or React/TypeScript if project scope supports it.
- **Database:** PostgreSQL; SQLite only for local development/demo data.
- **Jobs:** a bounded background queue such as Celery or RQ with Redis for task execution, limits, and retry management.
- **Deployment:** Docker Compose for local setup; managed HTTPS hosting for the portfolio demo.
- **Tests:** pytest for backend/unit tests, Playwright for key browser workflows, and lint/format checks in CI.

### 10.2 Architecture

Separate the web/API service from bounded background workers. The application creates a confirmed research job; workers retrieve only permitted passive source data through defined adapters and normalize it into one result schema. Each source adapter must enforce source-specific terms, rate limits, timeouts, attribution, and error handling.

Core entities: `User`, `Organization`, `OrganizationMatch`, `ReconRun`, `ReconResult`, `ResultObservation`, `AnalystNote`, `AuthorizationAcknowledgement`, and `AuditEvent`.

### 10.3 Security, privacy, and reliability controls

- Use HTTPS, secure session cookies, CSRF protection for browser forms, Argon2/bcrypt password hashing, and parameterized database access.
- Validate and canonicalize user input; protect all outbound retrieval from SSRF, redirects to private/reserved addresses, and unbounded requests.
- Use strict source allowlists, request budgets, per-user rate limits, task timeouts, concurrency limits, and a global kill switch.
- Respect source terms, robots controls where applicable, and applicable privacy/data-protection obligations.
- Redact sensitive values, minimize retained source content, encrypt stored data as appropriate, and establish retention/deletion rules.
- Log security-relevant events without storing passwords, tokens, secrets, or unnecessary sensitive source content.
- Include dependency scanning, secret scanning, and an OWASP-oriented review checklist in CI.

## 11. Acceptance criteria for the MVP

- A user can search by company name, review likely matches, and confirm the intended organization before a run starts.
- Public Profile mode returns only conservative, high-level organizational information and visibly states its limitations.
- Authorized Passive Recon mode requires a recorded acknowledgement before fuller passive result categories are available.
- The tool does not actively scan, probe, authenticate to, exploit, or otherwise interact with target systems beyond permitted passive public-source retrieval.
- Results are organized through the defined left-side categories and include source attribution and discovery time.
- A signed-in user can save a run, view prior runs, compare changes, and add text-only notes.
- The interface uses the defined cream, orange, and white visual system and works accessibly on current desktop and mobile browsers.
- A demo environment uses only mock data or intentionally controlled sources; it never targets arbitrary organizations.

## 12. Delivery phases

1. **Foundation:** authentication, responsive cream/orange/white interface, database schema, audit log, and mocked demo data.
2. **Search and confirmation:** company-name search, organization-match cards, target confirmation, and access-mode selection.
3. **Passive-recon pipeline:** bounded source adapters, normalized results, source attribution, discovery timestamps, and safe worker controls.
4. **Research workspace:** left navigation, category views, filtering, notes, saved runs, and change comparison.
5. **Portfolio polish:** test coverage, accessible UI review, CI, Docker documentation, threat model, source-policy documentation, and a short architecture case study.

## 13. Risks and decisions to revisit

- Public-source availability, terms, rate limits, and accuracy vary. The product must clearly show source attribution and avoid implying complete coverage.
- Organization matching can be ambiguous; user confirmation and confidence indicators are essential.
- Even public professional information can create privacy risk when aggregated. Apply minimization, clear source attribution, reporting/suppression controls, and strict exclusion of sensitive personal data.
- Document upload increases malware, privacy, and retention risk and must not be added without dedicated controls.
- Before a public launch, obtain a security review, publish an acceptable-use policy and privacy policy, set an abuse-reporting path, and verify source compliance.

## 14. Portfolio narrative

The project should be presented as an authorization-aware passive-reconnaissance research platform, not as a hacking tool. Highlight the product judgment behind it: target confirmation, two-tier access modes, passive-only boundaries, source provenance, privacy-aware data handling, bounded workers, saved-run comparisons, and an accessible research-focused interface. These decisions demonstrate the security-minded engineering and analyst workflow awareness expected by cybersecurity employers.
