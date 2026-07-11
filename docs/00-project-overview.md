# Project Overview

**Project Name:** SecPod QA Test Management & Automation Platform (working title: "QualityHub")
**Version:** 0.1.0 (Initial Development)
**Status:** In Development
**Tagline:** One platform to plan, run, and track every test — manual or automated — across SecPod's cybersecurity product suite.

*(Name assumed as a placeholder — adjust if SecPod has a preferred internal project name)*

---

## What Is This?

QualityHub is an internal web platform for SecPod's QA team that centralizes manual test case management,
automated test result ingestion, defect visibility, and release-readiness reporting for SecPod's unified
endpoint security platform.

| Use Case | Description |
|---|---|
| Manual Test Execution | QA engineers create test cases, execute them against a build, and log pass/fail results with evidence |
| Automated Test Reporting | Automation scripts (Python/Java, Selenium/TestNG/JUnit) POST results to the API after each CI run |
| Coverage Dashboard | QA leads view test coverage by application module, release, and test type (manual vs. automated) |
| Defect Tracking | Failed test cases automatically generate linked defect records for triage |
| AI-Assisted Test Authoring | QA engineers describe a feature/requirement in plain language and get a draft test case via the AI Playground |
| Onboarding Reference | New hires browse existing test suites, conventions, and past run history to ramp up quickly |

*(Table rows replaced with project-specific use cases per template instructions)*

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.14+ |
| **Web Framework** | FastAPI (≥ 0.138.0) + Uvicorn (ASGI) |
| **Frontend** | HTMX + Jinja2 templates + Tailwind CSS |
| **Database (Dev)** | SQLite via `aiosqlite` (async, zero-config) |
| **Database (Prod)** | PostgreSQL via `asyncpg` (async) |
| **ORM** | SQLAlchemy 2.0 (fully async) |
| **Migrations** | Alembic |
| **Validation** | Pydantic v2 + `pydantic-settings` + `email-validator` |
| **Auth** | JWT (`pyjwt[crypto]`, HS256+) + bcrypt (cost ≥ 12) |
| **Cache / Broker** | Redis |
| **AI / LLM** | Pluggable: Mock (default, no API key) → OpenAI → Anthropic (via `AI_PROVIDER` env var) — used here for AI-assisted test-case drafting and failure-pattern summarization |
| **HTTP Client** | httpx (async, used for LLM provider calls and for automation clients reporting results) |
| **Form Parsing** | `python-multipart` (used for test-evidence/screenshot uploads) |
| **Containers** | Podman + Podman Compose (Dockerfile also provided) |
| **Reverse Proxy** | Caddy |
| **CI/CD** | GitHub Actions — automation suites (Selenium/TestNG/JUnit) call the platform's API at the end of each pipeline run |
| **Testing** | pytest + pytest-asyncio + anyio |
| **Linting** | Ruff (target: Python 3.14, line-length: 100) |
| **Logging** | `python-json-logger` (structured JSON logs) |
| **Config** | `python-dotenv` + Pydantic Settings (12-Factor App pattern) |

**Project-specific additions:**
- Selenium / TestNG / JUnit remain in the QA engineers' own automation repos; they integrate with QualityHub only via its REST API (no new framework dependency added to the template stack).

*(Assumed integration boundary — adjust if automation scripts should live inside this repo)*

---

## Key Features

- **Test Case Management** — create, edit, tag, and organize manual test cases by module, priority, and release
- **Test Run Execution** — step-by-step manual execution UI (HTMX partial updates) with pass/fail/blocked status and evidence attachment
- **Automated Result Ingestion API** — `/api/v1/test-runs` endpoint for CI pipelines to report automated results
- **Coverage & Trends Dashboard** — visual summary of pass/fail rates, coverage by module, and trends across releases
- **Defect Linking** — failed test cases can be linked to defect records with status tracking
- **AI Test-Case Drafting** — generate a draft test case from a plain-language requirement description
- **AI Failure-Pattern Summary** — summarize recurring failure themes across recent automated runs
- **Role-Based Access Control** — QA Engineer, QA Lead, and Admin roles with appropriate permissions
- **Release Readiness View** — snapshot of open defects and test coverage gaps before a release sign-off
- **REST API** — full `/api/v1/` surface with auto-generated OpenAPI docs for integrating external automation tools

*(Generic feature list replaced with project-specific features per template instructions)*

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/secpod/qualityhub.git
cd qualityhub

# Copy environment template
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload

# Or run with Podman Compose (recommended for full stack incl. PostgreSQL + Redis)
podman-compose up --build
```

Visit `http://localhost:8000` for the dashboard and `http://localhost:8000/docs` for the auto-generated OpenAPI documentation.

*(Repo URL and project name are placeholders — adjust to actual SecPod repository details)*

---

## Architecture Summary

```
app/
├── core/           # Config (Pydantic Settings), DB engine, security (JWT/bcrypt)
├── models/         # SQLAlchemy ORM models: TestCase, TestRun, Defect, User, Release
├── repositories/   # Data access layer (BaseRepository[T] + TestCaseRepository, TestRunRepository, DefectRepository)
├── schemas/        # Pydantic v2 schemas (Create / Read / Update) for test cases, runs, defects
├── services/       # Business logic: AuthService, TestCaseService, TestRunService, DefectService, AIService (test-case drafting + failure summarization)
├── api/
│   ├── endpoints/  # JSON REST API routes (/api/v1/) — auth, test-cases, test-runs, defects, ai
│   └── views/      # Jinja2 HTML view routes (HTMX-powered) — dashboard, test execution UI, coverage reports
├── background/     # Async workers — e.g., recomputing coverage stats after new test runs land
├── templates/      # Jinja2 HTML (base.html, auth/, dashboard/, test-cases/, ai/)
├── static/         # CSS, JS assets
└── utils/          # Structured logging, helpers
```

Each module maps directly to a QA workflow concern: `models`/`repositories`/`services` handle test cases,
runs, and defects as first-class domain objects; `api/endpoints` is the integration point for CI-driven
automation; `api/views` + `templates` serve the human-facing dashboard used day-to-day by QA engineers and leads.

*(Directory tree kept identical to template; annotations added per template instructions)*
