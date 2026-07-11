# Requirements

## Functional Requirements

| ID | Requirement | Description | Priority |
|---|---|---|---|
| FR-001 | User Authentication | Users register/login via JWT-based auth (access + refresh tokens), bcrypt-hashed passwords, RBAC with QA Engineer / QA Lead / Admin roles | Must Have |
| FR-002 | Test Case Management | Users can create, edit, tag (module, priority, type), archive, and search manual test cases | Must Have |
| FR-003 | Manual Test Execution | Users can execute a test case step-by-step, record pass/fail/blocked status, attach evidence (screenshots/logs), and add notes per run | Must Have |
| FR-004 | Automated Result Ingestion | The API accepts automated test run results (`POST /api/v1/test-runs`) from CI pipelines, including status, duration, logs, and linked build/release identifier | Must Have |
| FR-005 | Defect Linking | A failed test case run can be linked to a new or existing defect record with status (Open, Triaged, Fixed, Verified, Closed) | Must Have |
| FR-006 | Coverage & Trends Dashboard | Users can view test coverage by module and release, and pass/fail trends over time, via HTMX-powered charts/tables | Must Have |
| FR-007 | AI-Assisted Test Case Drafting | Users submit a plain-language requirement description and receive a draft test case (steps, expected results) via the pluggable AI provider | Should Have |
| FR-008 | AI Failure-Pattern Summarization | Users request a summary of recurring failure themes across a set of recent automated test runs | Should Have |
| FR-009 | Release Readiness View | Users can view a snapshot of open defects and coverage gaps for a specific release before sign-off | Should Have |
| FR-010 | Test Suite Export/Import | Users can export a set of test cases (e.g., CSV/JSON) for sharing or offline review, and re-import edited sets | Could Have |

*(FR-001 kept close to template baseline per instructions; FR-002 onward are project-specific)*

---

## Non-Functional Requirements

### Performance

| ID | Requirement | Target |
|---|---|---|
| NFR-001 | API response time | 95th percentile < 300ms for standard CRUD endpoints under normal load |
| NFR-002 | Automated result ingestion throughput | Support at least 50 concurrent CI-triggered test-run submissions without degradation |
| NFR-003 | Dashboard load time | Coverage dashboard renders in < 2s for a release with up to 5,000 test cases |

### Security

| ID | Requirement | Target |
|---|---|---|
| NFR-004 | Password storage | bcrypt with cost factor ≥ 12 |
| NFR-005 | Token security | JWT access tokens short-lived (≤ 15 min), refresh tokens rotated, HS256 or stronger |
| NFR-006 | Transport security | All traffic served over HTTPS in production (via Caddy reverse proxy) |
| NFR-007 | Input validation | All API inputs validated via Pydantic v2 schemas; no raw SQL string interpolation |
| NFR-008 | Access control | RBAC enforced on all endpoints; QA Engineers cannot modify Admin-only settings |

### Reliability & Availability

| ID | Requirement | Target |
|---|---|---|
| NFR-009 | Uptime | 99.5% availability during business hours (internal tool, not customer-facing) |
| NFR-010 | Data durability | PostgreSQL backups on a daily schedule in production; point-in-time recovery supported |
| NFR-011 | Graceful degradation | If the AI provider is unreachable, AI-assisted features fail gracefully with a clear error, without blocking core test management functions |

### Maintainability & Observability

| ID | Requirement | Target |
|---|---|---|
| NFR-012 | Structured logging | All requests and background jobs log structured JSON via `python-json-logger` |
| NFR-013 | Health monitoring | `/health` endpoint reports DB, Redis, and AI provider connectivity status |
| NFR-014 | Code quality | Ruff linting enforced in CI; line length 100, target Python 3.14 |
| NFR-015 | Test coverage (of QualityHub itself) | Minimum 80% coverage on `services/` and `repositories/` layers via pytest |

*(NFR sections replaced with project-specific performance, security, reliability, and maintainability targets per template instructions)*
