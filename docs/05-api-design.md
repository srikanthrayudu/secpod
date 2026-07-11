# API Design

## Overview

All endpoints are versioned under `/api/v1/`. Authentication uses JWT bearer tokens (access + refresh).
Auth endpoints are carried over from the template baseline; domain-specific endpoints below cover test cases,
test runs, defects, releases, and AI-assisted features. Full interactive documentation is auto-generated at
`/docs` (Swagger UI) and `/redoc`.

---

## Auth Endpoints (Template Baseline)

| Method | Path | Auth Required | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | No | Register a new user (QA Engineer by default; Admin can elevate role) |
| POST | `/api/v1/auth/login` | No | Authenticate, returns access + refresh JWT tokens |
| POST | `/api/v1/auth/refresh` | Refresh token | Issue a new access token |
| POST | `/api/v1/auth/logout` | Yes | Invalidate refresh token |
| GET | `/api/v1/auth/me` | Yes | Return current authenticated user's profile and role |

---

## Test Case Endpoints

| Method | Path | Auth Required | Request Body | Response | Description |
|---|---|---|---|---|---|
| GET | `/api/v1/test-cases` | Yes | Query params: `module`, `priority`, `type`, `search` | List of `TestCaseRead` | List/search/filter test cases |
| POST | `/api/v1/test-cases` | Yes (QA Engineer+) | `TestCaseCreate` (title, module, priority, steps, expected_result, tags) | `TestCaseRead` | Create a new manual test case |
| GET | `/api/v1/test-cases/{id}` | Yes | — | `TestCaseRead` | Get a single test case with full step details |
| PATCH | `/api/v1/test-cases/{id}` | Yes (QA Engineer+) | `TestCaseUpdate` | `TestCaseRead` | Edit a test case |
| DELETE | `/api/v1/test-cases/{id}` | Yes (QA Lead/Admin) | — | 204 No Content | Archive/delete a test case |

---

## Test Run Endpoints

| Method | Path | Auth Required | Request Body | Response | Description |
|---|---|---|---|---|---|
| POST | `/api/v1/test-runs` | Yes (API token; used by CI or dashboard) | `TestRunCreate` (test_case_id, release_id, status, duration_ms, logs, source: manual\|automated) | `TestRunRead` | Report a test run result (manual submission or automated CI ingestion) |
| GET | `/api/v1/test-runs` | Yes | Query params: `release_id`, `status`, `source`, `module` | List of `TestRunRead` | List test run history with filters |
| GET | `/api/v1/test-runs/{id}` | Yes | — | `TestRunRead` | Get details of a single test run, incl. evidence attachments |
| POST | `/api/v1/test-runs/{id}/evidence` | Yes | Multipart form (`python-multipart`) | `EvidenceRead` | Attach a screenshot/log file to a test run |

---

## Defect Endpoints

| Method | Path | Auth Required | Request Body | Response | Description |
|---|---|---|---|---|---|
| POST | `/api/v1/defects` | Yes | `DefectCreate` (title, description, test_run_id, severity) | `DefectRead` | Create a defect, optionally linked to a failed test run |
| GET | `/api/v1/defects` | Yes | Query params: `status`, `severity`, `release_id` | List of `DefectRead` | List/filter defects |
| PATCH | `/api/v1/defects/{id}` | Yes (QA Lead/Admin) | `DefectUpdate` (status: Open\|Triaged\|Fixed\|Verified\|Closed) | `DefectRead` | Update defect status/details |

---

## Release Endpoints

| Method | Path | Auth Required | Request Body | Response | Description |
|---|---|---|---|---|---|
| POST | `/api/v1/releases` | Yes (QA Lead/Admin) | `ReleaseCreate` (name, target_date) | `ReleaseRead` | Create a new release for tracking |
| GET | `/api/v1/releases/{id}/readiness` | Yes | — | `ReleaseReadiness` (coverage %, open defects, pass rate) | Get release-readiness snapshot |

---

## AI Endpoints

| Method | Path | Auth Required | Request Body | Response | Description |
|---|---|---|---|---|---|
| POST | `/api/v1/ai/draft-test-case` | Yes | `{ "requirement_text": str }` | `{ "draft_steps": [...], "expected_result": str }` | Generate a draft test case from a plain-language requirement |
| POST | `/api/v1/ai/summarize-failures` | Yes | `{ "release_id": uuid, "limit": int }` | `{ "summary": str, "themes": [...] }` | Summarize recurring failure themes across recent automated runs |

---

## Health Endpoint

| Method | Path | Auth Required | Response | Description |
|---|---|---|---|---|
| GET | `/health` | No | `{ "status": "ok", "db": "ok", "redis": "ok", "ai_provider": "ok" }` | Reports connectivity status of DB, Redis, and AI provider |

*(All endpoints beyond Auth are project-specific per template instructions; Auth kept as template baseline)*
