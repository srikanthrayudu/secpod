# Security

## Auth Model

QualityHub uses the template's baseline authentication approach, confirmed applicable to this project:

- **JWT-based auth** — short-lived access tokens (≤ 15 min) plus rotated refresh tokens, signed with HS256 or stronger (`pyjwt[crypto]`).
- **Password hashing** — bcrypt with cost factor ≥ 12 for all stored credentials.
- **RBAC** — three roles (`qa_engineer`, `qa_lead`, `admin`) enforced at the API layer via dependency-injected
  permission checks; e.g., only `qa_lead`/`admin` can update defect status or delete test cases.
- **Session handling** — HTTP-only, SameSite cookies for the browser dashboard session; bearer tokens for
  programmatic API/CI access.

*(Confirmed applicable per template instructions — no changes needed to the baseline auth model)*

---

## Threat Model & Mitigations

| Threat | Description | Mitigation |
|---|---|---|
| Credential stuffing / brute force login | Automated login attempts against QA accounts | Rate limiting on `/api/v1/auth/login` (Redis-backed), account lockout after repeated failures |
| Unauthorized test/defect data modification | A QA Engineer account modifying data outside its role scope | RBAC enforced server-side on every mutating endpoint, not just hidden in UI |
| Leaked CI automation tokens | A long-lived API token used by CI pipelines to report test runs is exposed in logs or a public repo | Scoped, revocable service tokens for CI (separate from user JWTs); tokens never logged; stored as CI secrets |
| Evidence file upload abuse | Malicious file uploaded as "evidence" (e.g., oversized file, executable disguised as screenshot) | File type allow-list, size limits, and storage outside the web root; served via signed URLs, not direct static paths |
| Injection via test case fields (steps, logs) | Stored XSS via test case description or automated log output rendered in the dashboard | Jinja2 autoescaping (template default) + input validation via Pydantic; logs rendered as escaped text, not raw HTML |
| AI prompt injection via requirement text | A crafted "requirement" submitted to the AI draft-test-case feature attempts to manipulate the LLM provider | Treat AI output as a draft only, never auto-executed or auto-published; user must review/edit before saving as a real test case |
| Data exfiltration via API | A compromised account scrapes all test cases/defects via the API | Pagination enforced on list endpoints, rate limiting per user/token, audit logging of bulk exports |

*(Threat model tailored to QualityHub's specific attack surface — CI token handling, evidence uploads, AI drafting — per template instructions)*

---

## Data Sensitivity Classification

| Data Type | Classification | Notes |
|---|---|---|
| User credentials (password hashes) | Restricted | Never logged, bcrypt-hashed at rest |
| Test case content, steps | Internal | May reference SecPod's proprietary platform internals; not for external sharing |
| Test run logs / evidence | Internal | May contain application internals or, rarely, sanitized-but-sensitive debug output |
| Defect descriptions | Internal | May reference unpatched vulnerabilities in SecPod's own product — treated as sensitive until resolved |
| AI-generated content (drafts, summaries) | Internal | Subject to same handling as the source test case/run data it's derived from |

*(Classification reflects that QualityHub itself may store references to unpatched security issues in SecPod's product, given SecPod's own domain — flagged as sensitive per template instructions)*

---

## Compliance Requirements

As an internal tool (not customer-facing, no end-customer PII processed), QualityHub has no direct external
compliance mandate (e.g., GDPR/HIPAA) by default. However, since SecPod is a cybersecurity company, the
following internal-hygiene practices are recommended:

- Treat defect records referencing security-relevant bugs in SecPod's own platform with the same access
  discipline SecPod expects from its customers (least privilege, audit trail on status changes).
- Retain test run and defect history per SecPod's internal data retention policy (not defined in this document —
  confirm with SecPod's compliance/security team).

*(No mandatory external compliance framework assumed, since this is an internal tool — adjust if SecPod has internal compliance policies that apply)*
