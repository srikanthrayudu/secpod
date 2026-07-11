# Test Plan

## Test Strategy

QualityHub's own test suite (distinct from the test cases QualityHub manages for SecPod's product) follows a
standard pyramid approach appropriate to a FastAPI + async SQLAlchemy application:

- **Unit Tests** — service-layer logic (e.g., `TestRunService` status transitions, `CoverageService` aggregation
  math, `AIService` provider-switching logic) tested in isolation with mocked repositories.
- **Integration Tests** — API endpoint tests against a real (test) database via `pytest-asyncio` + `anyio`,
  covering the full request → service → repository → DB path for test cases, test runs, defects, and releases.
- **End-to-End Tests** — critical user flows (login → create test case → execute → mark failed → link defect →
  view on dashboard) run against a running instance, using the same HTTP client patterns automation engineers
  would use against the real API.

*(Strategy scoped to testing QualityHub itself, not the SecPod product it manages test cases for — per template instructions)*

---

## Test Case Table (Domain-Specific)

| Test ID | Feature | Scenario | Expected Result |
|---|---|---|---|
| TC-001 | Auth | Register with valid email/password | User created, 201 response, no password in response body |
| TC-002 | Auth | Login with correct credentials | Access + refresh JWT returned |
| TC-003 | Auth | Login with incorrect password | 401 Unauthorized |
| TC-004 | Test Case CRUD | QA Engineer creates a test case | 201 response, test case persisted with correct `created_by` |
| TC-005 | Test Case CRUD | QA Engineer attempts to delete a test case | 403 Forbidden (delete restricted to QA Lead/Admin) |
| TC-006 | Test Run — Manual | QA Engineer executes a test case, marks step "Failed" | Test run stored with `source=manual`, `status=failed` |
| TC-007 | Test Run — Automated | CI posts a test run via API with valid service token | 201 response, `source=automated` stored correctly |
| TC-008 | Test Run — Automated | CI posts a test run with invalid/expired token | 401 Unauthorized |
| TC-009 | Defect Linking | Failed test run linked to a new defect | Defect created with correct `test_run_id`, `status=open` |
| TC-010 | Defect Status | QA Lead updates defect status to "Verified" | Status updated, `resolved_at` unset until "Closed" |
| TC-011 | Coverage Dashboard | Dashboard requested after several test runs recorded | Correct pass/fail percentages returned per module |
| TC-012 | AI Draft Test Case | Submit requirement text | Draft steps + expected result returned; mock provider used in test env |
| TC-013 | AI Failure Summary | Request summary for a release with failed runs | Summary text + themes list returned |
| TC-014 | Evidence Upload | Upload a valid PNG under size limit | 201 response, file stored, linked to test run |
| TC-015 | Evidence Upload | Upload an oversized or disallowed file type | 400/413 rejection with clear error message |

*(Test cases specific to QualityHub's own domain features per template instructions)*

---

## Coverage Targets

| Layer | Target Coverage |
|---|---|
| `services/` | ≥ 80% |
| `repositories/` | ≥ 80% |
| `api/endpoints/` | ≥ 70% (integration tests) |
| Overall project | ≥ 75% |

*(Aligned with NFR-015 from the requirements document)*

---

## How to Run Tests Locally

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run full test suite
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run only unit tests (services layer)
pytest tests/unit

# Run only integration tests (API + DB)
pytest tests/integration

# Lint check (Ruff)
ruff check .
```

Tests use a separate SQLite test database (or an ephemeral PostgreSQL container in CI) so they never touch
development or production data. The `AI_PROVIDER` environment variable defaults to `mock` in the test
environment, so AI-dependent tests run deterministically without external API calls.

*(Local test commands consistent with the template's pytest + pytest-asyncio + anyio + Ruff baseline)*
