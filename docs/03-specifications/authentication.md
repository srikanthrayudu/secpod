# Specification: Authentication

## Purpose
Defines the authentication and authorization behavior for QualityHub, covering user-facing login as well as
service-to-service access for CI automation pipelines.

## Scope
Covers registration, login, token issuance/refresh, logout, RBAC enforcement, and CI service-token access.
Does not cover feature-level permissions beyond role checks (those are documented per-feature where relevant).

---

## User Roles

| Role | Description | Typical Permissions |
|---|---|---|
| `qa_engineer` | Standard QA team member | Create/edit test cases, execute manual runs, create defects |
| `qa_lead` | QA team lead/manager | All QA Engineer permissions + update defect status, delete test cases, manage releases |
| `admin` | Platform administrator | All permissions, including user management |

*(Roles adjusted from the template's generic RBAC to QualityHub's QA-domain roles)*

---

## Functional Behavior

| Behavior | Detail |
|---|---|
| Registration | New users register with email + password; default role is `qa_engineer` unless elevated by an Admin |
| Login | Email + password validated against bcrypt hash; on success, an access token (JWT) and refresh token are issued |
| Access token | Short-lived (≤ 15 minutes), signed HS256+, contains `sub` (user id) and `role` claims |
| Refresh token | Longer-lived (7 days default), used to obtain a new access token without re-entering credentials; rotated on each use |
| Logout | Invalidates the current refresh token (server-side revocation list in Redis) |
| Password hashing | bcrypt with cost factor ≥ 12 (NFR-004) |
| RBAC enforcement | Every mutating endpoint checks the `role` claim server-side via a dependency; UI-level hiding of controls is not treated as sufficient enforcement |

## CI Service Tokens

| Behavior | Detail |
|---|---|
| Purpose | Allow CI pipelines (Selenium/TestNG/JUnit automation) to call `POST /api/v1/test-runs` without a human user session |
| Issuance | A scoped, revocable service token is generated per CI pipeline/project, signed using `CI_SERVICE_TOKEN_SECRET` |
| Scope | Service tokens are restricted to the test-run ingestion endpoint only — they cannot access user management, defect status changes, or other user-scoped actions |
| Rotation | Tokens are rotatable independently of user credentials; revoking one token does not affect others |
| Storage | Tokens are stored only in the CI platform's secrets manager, never committed to source control or written to logs |

## Session Handling

| Context | Mechanism |
|---|---|
| Browser dashboard | HTTP-only, SameSite cookies carrying the access token |
| API / CI clients | Bearer token in the `Authorization` header |

## Error Handling

| Condition | Response |
|---|---|
| Invalid credentials | `401 Unauthorized` |
| Expired access token | `401 Unauthorized` — client should use refresh token to obtain a new one |
| Expired/revoked refresh token | `401 Unauthorized` — user must log in again |
| Insufficient role for an action | `403 Forbidden` |
| Invalid/expired CI service token | `401 Unauthorized` |

## Non-Functional Notes
- Rate limiting on `/api/v1/auth/login` (Redis-backed) to mitigate brute-force/credential-stuffing attempts.
- All auth-related failures logged (without credentials) via structured JSON logging for audit purposes.

*(Generated based on FR-001 in `docs/02-requirements.md`, NFR-004/005/008, and the Auth section of `docs/08-security.md`)*
