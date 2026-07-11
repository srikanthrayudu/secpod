# Architecture

## Architecture Overview

QualityHub follows the template's Modular Monolith / Clean Architecture pattern. The system is composed of a
single FastAPI application organized into clearly separated layers, backed by PostgreSQL (production) or SQLite
(development), with Redis for caching and background task coordination.

At a high level:

- **QA Engineers and Leads** interact with the system through the **HTMX/Jinja2 web dashboard** (`api/views`) —
  creating test cases, executing manual runs, and viewing coverage/trend reports.
- **CI/CD pipelines** (GitHub Actions running Selenium/TestNG/JUnit suites) interact with the system through the
  **REST API** (`api/endpoints`) — posting automated test run results after each build.
- Both paths flow through the same **service layer**, ensuring manual and automated results are validated,
  stored, and reported on consistently.
- The **AI service** (pluggable Mock → OpenAI → Anthropic) supports test-case drafting and failure-pattern
  summarization, called from both the dashboard and, optionally, the API.
- A **background worker** recomputes coverage/trend aggregates asynchronously whenever new test runs land, so
  the dashboard stays responsive without recalculating on every page load.

*(Architecture description tailored to QualityHub's dual manual/automated ingestion paths per template instructions)*

---

## Layer Responsibilities

| Layer | Responsibility |
|---|---|
| `core/` | App configuration (Pydantic Settings), async DB engine setup, JWT/bcrypt security utilities |
| `models/` | SQLAlchemy ORM models: `User`, `TestCase`, `TestRun`, `Defect`, `Release` — all with UUID PKs and timestamps |
| `repositories/` | `BaseRepository[T]` plus `TestCaseRepository`, `TestRunRepository`, `DefectRepository`, `ReleaseRepository` — encapsulate all DB access |
| `schemas/` | Pydantic v2 Create/Read/Update schemas for test cases, test runs, defects, releases |
| `services/` | `AuthService` (login/register/RBAC), `TestCaseService` (CRUD + tagging), `TestRunService` (manual execution + automated ingestion), `DefectService` (linking + status transitions), `CoverageService` (aggregate stats), `AIService` (test-case drafting, failure summarization via pluggable LLM provider) |
| `api/endpoints/` | JSON REST routes: `/api/v1/auth`, `/api/v1/test-cases`, `/api/v1/test-runs`, `/api/v1/defects`, `/api/v1/releases`, `/api/v1/ai`, `/health` |
| `api/views/` | Jinja2 HTML routes rendering the dashboard, test-case management UI, test execution flow, and coverage reports, with HTMX partials for interactive updates |
| `background/` | Async worker(s) that recompute coverage/trend aggregates and can notify QA Leads (e.g., via Redis pub/sub) when a release's defect count crosses a threshold |
| `templates/` | `base.html`, `auth/`, `dashboard/`, `test-cases/`, `ai/` — Jinja2 templates for each UI area |
| `static/` | Tailwind-compiled CSS, JS assets |
| `utils/` | Structured JSON logging helpers, shared utilities |

*(Generic `AIService` and layer descriptions replaced with QualityHub-specific services per template instructions)*

---

## Directory Structure

```
app/
├── core/
│   ├── config.py
│   ├── db.py
│   └── security.py
├── models/
│   ├── user.py
│   ├── test_case.py
│   ├── test_run.py
│   ├── defect.py
│   └── release.py
├── repositories/
│   ├── base.py
│   ├── test_case_repository.py
│   ├── test_run_repository.py
│   ├── defect_repository.py
│   └── release_repository.py
├── schemas/
│   ├── user.py
│   ├── test_case.py
│   ├── test_run.py
│   ├── defect.py
│   └── release.py
├── services/
│   ├── auth_service.py
│   ├── test_case_service.py
│   ├── test_run_service.py
│   ├── defect_service.py
│   ├── coverage_service.py
│   └── ai_service.py
├── api/
│   ├── endpoints/
│   │   ├── auth.py
│   │   ├── test_cases.py
│   │   ├── test_runs.py
│   │   ├── defects.py
│   │   ├── releases.py
│   │   ├── ai.py
│   │   └── health.py
│   └── views/
│       ├── dashboard.py
│       ├── test_cases.py
│       ├── test_execution.py
│       └── coverage.py
├── background/
│   └── coverage_worker.py
├── templates/
│   ├── base.html
│   ├── auth/
│   ├── dashboard/
│   ├── test-cases/
│   └── ai/
├── static/
└── utils/
    └── logging.py
```

*(Directory structure expanded from the template baseline to show QualityHub's new services/endpoints/models per template instructions)*

---

## Scaling Strategy

| Concern | Strategy | Target Load |
|---|---|---|
| Concurrent users | Internal QA team tool; horizontal scaling of Uvicorn workers behind Caddy if needed | Up to ~100 concurrent internal users |
| Automated result ingestion spikes | Redis-backed queue absorbs bursts from CI pipelines triggering many parallel test suites | Up to 50 concurrent automated submissions |
| Database growth | PostgreSQL with indexes on `test_case_id`, `release_id`, `created_at`; partitioning considered if `test_run` history exceeds ~10M rows | Multi-year history across releases |
| Coverage computation | Offloaded to async background worker rather than computed per-request | Recompute triggered per new test run batch, not per page view |
| AI provider calls | Rate-limited and cached (Redis) per requirement/test-case-draft request to avoid redundant LLM calls | N/A (internal, low-frequency use) |

*(Scaling targets sized for an internal QA tool rather than a customer-facing platform, per the project's actual expected load)*
