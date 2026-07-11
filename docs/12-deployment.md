# Deployment

## Local Development Setup

```bash
# Clone the repository
git clone https://github.com/secpod/qualityhub.git
cd qualityhub

# Copy environment template and configure
cp .env.example .env
# Edit .env: set DATABASE_URL (SQLite default), JWT_SECRET, AI_PROVIDER=mock, etc.

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` for the dashboard, `http://localhost:8000/docs` for the OpenAPI documentation,
and `http://localhost:8000/health` to confirm DB/Redis/AI provider connectivity.

*(Local setup consistent with template baseline; project name/URL adjusted)*

---

## Container-Based Deployment (Podman Compose)

```bash
# Build and start the full stack (app + PostgreSQL + Redis + Caddy)
podman-compose up --build

# Run migrations inside the running app container
podman-compose exec app alembic upgrade head

# View logs (structured JSON)
podman-compose logs -f app

# Stop the stack
podman-compose down
```

`podman-compose.yml` defines four services: `app` (FastAPI/Uvicorn), `db` (PostgreSQL via `asyncpg`), `redis`
(cache/broker), and `caddy` (reverse proxy + automatic HTTPS in production).

*(Deployment steps consistent with template's Podman + Podman Compose baseline)*

---

## Environment Variable Reference

| Variable | Description | Example / Default |
|---|---|---|
| `DATABASE_URL` | Async DB connection string | `postgresql+asyncpg://user:pass@db:5432/qualityhub` (prod), `sqlite+aiosqlite:///./dev.db` (dev) |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `JWT_SECRET` | Secret key for signing JWTs | (generated, kept in CI/production secrets store) |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `BCRYPT_COST` | bcrypt hashing cost factor | `12` |
| `AI_PROVIDER` | Selects LLM backend | `mock` \| `openai` \| `anthropic` |
| `AI_API_KEY` | API key for chosen AI provider (unused if `mock`) | (secret) |
| `CI_SERVICE_TOKEN_SECRET` | Secret used to issue/validate scoped CI service tokens for automated test-run ingestion | (secret) |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `CORS_ORIGINS` | Allowed origins for CORS | `https://qualityhub.internal.secpod.com` |

*(Includes project-specific `CI_SERVICE_TOKEN_SECRET` in addition to template baseline variables)*

---

## Production Checklist

- [ ] `JWT_SECRET` and `CI_SERVICE_TOKEN_SECRET` set via a secrets manager, not committed to `.env` in repo
- [ ] `DATABASE_URL` points to production PostgreSQL with automated daily backups configured
- [ ] `AI_PROVIDER` set to the intended production provider (`openai` or `anthropic`), with valid `AI_API_KEY`
- [ ] Caddy configured with valid domain and automatic HTTPS (Let's Encrypt) enabled
- [ ] `alembic upgrade head` run as a deploy step before app restart
- [ ] `/health` endpoint checked post-deploy (DB, Redis, AI provider all `ok`)
- [ ] Rate limiting on `/api/v1/auth/login` and `/api/v1/test-runs` confirmed active
- [ ] Structured JSON logs shipped to SecPod's internal log aggregation (if applicable)
- [ ] CI service tokens for automated ingestion issued and rotated per SecPod's internal security policy
- [ ] Backup restore procedure tested at least once before go-live

*(Checklist tailored to QualityHub's specific secrets and integration points per template instructions)*
