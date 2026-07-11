# QualityHub

**SecPod QA Test Management & Automation Platform**

QualityHub is an internal web platform for SecPod's QA team. It centralizes manual test case management, automated test result ingestion, defect visibility, and release-readiness reporting.

## Quick Start

```bash
chmod +x scripts/run_dev.sh
./scripts/run_dev.sh
```

- **URL:** http://localhost:8000
- **API docs:** http://localhost:8000/docs
- **Admin:** `admin@qualityhub.local` / `password123`
- **QA Lead:** `lead@qualityhub.local` / `password123`
- **QA Engineer:** `engineer@qualityhub.local` / `password123`

## Features

- Test case CRUD with tagging, modules, and priorities
- Manual test execution with pass/fail/blocked recording
- Automated result ingestion via `POST /api/v1/test-runs`
- Defect linking with auto-creation on failed runs
- Release readiness snapshots (coverage, pass rate, open defects)
- AI-assisted test case drafting and failure summarization
- Role-based access: QA Engineer, QA Lead, Admin

## Technology Stack

- **Backend:** Python 3.14+, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2
- **Frontend:** Jinja2, HTMX, Tailwind CSS, Alpine.js
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Cache:** Redis
- **AI:** Pluggable Mock / OpenAI / Anthropic via `DEFAULT_LLM_PROVIDER`
- **Testing:** pytest + pytest-asyncio

## Project Structure

```text
app/
├── core/           # Config, database, security, seeding
├── models/         # TestCase, TestRun, Defect, Release, Evidence, User
├── repositories/   # Data access layer
├── schemas/        # Pydantic request/response models
├── services/       # Business logic (QA + Auth + AI)
├── api/
│   ├── endpoints/  # REST API (/api/v1/)
│   └── views/      # HTMX dashboard views
└── templates/      # Jinja2 HTML templates
docs/               # Full project documentation
tests/              # pytest suite
```

## Configuration

Copy `.env.example` to `.env` and set at minimum:

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key (64+ char random string) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./sqlite.db` for local dev |
| `DEFAULT_LLM_PROVIDER` | `mock`, `openai`, or `anthropic` |

## Testing

```bash
pytest -v
```

## Documentation

See the `docs/` directory for architecture, API design, database schema, security model, and roadmap.
