# Database Design

## ERD (Text/ASCII)

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│    User     │       │  TestCase    │       │   Release   │
├─────────────┤       ├──────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)      │       │ id (PK)     │
│ email       │       │ title        │       │ name        │
│ password_   │       │ module       │       │ target_date │
│   hash      │       │ priority     │       │ status      │
│ role        │       │ steps (JSON) │       │ created_at  │
│ created_at  │       │ expected_    │       └──────┬──────┘
└──────┬──────┘       │   result     │              │
       │              │ tags (JSON)  │              │ 1
       │ 1            │ created_by ──┼──────┐       │
       │              │   (FK->User) │      │       │
       │              │ created_at   │      │       │
       │              └──────┬───────┘      │       │
       │                     │ 1            │       │
       │                     │              │       │
       │                     │ N            │       │
       │              ┌──────┴───────┐      │       │ N
       │ N            │   TestRun    │      │  ┌─────┴──────┐
       └──────────────┤              ├──────┘  │  Defect    │
        (executed_by) │ id (PK)      │         ├────────────┤
                      │ test_case_id │ N     1 │ id (PK)    │
                      │   (FK)       ├─────────┤ title      │
                      │ release_id   │         │ description│
                      │   (FK)       │         │ severity   │
                      │ status       │         │ status     │
                      │ source       │         │ test_run_id│
                      │   (manual/   │         │   (FK)     │
                      │    automated)│         │ created_at │
                      │ duration_ms  │         │ resolved_at│
                      │ logs         │         └────────────┘
                      │ executed_by  │
                      │   (FK->User) │
                      │ created_at   │
                      └──────┬───────┘
                             │ 1
                             │
                             │ N
                      ┌──────┴───────┐
                      │  Evidence    │
                      ├──────────────┤
                      │ id (PK)      │
                      │ test_run_id  │
                      │   (FK)       │
                      │ file_path    │
                      │ file_type    │
                      │ uploaded_at  │
                      └──────────────┘
```

---

## Table Definitions

### `users`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL (bcrypt) |
| role | ENUM('qa_engineer', 'qa_lead', 'admin') | NOT NULL, default `qa_engineer` |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()` |

### `test_cases`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| title | VARCHAR(255) | NOT NULL |
| module | VARCHAR(100) | NOT NULL, indexed |
| priority | ENUM('low', 'medium', 'high', 'critical') | NOT NULL |
| steps | JSONB | NOT NULL (ordered list of step descriptions) |
| expected_result | TEXT | NOT NULL |
| tags | JSONB | nullable (array of strings) |
| created_by | UUID | FK → `users.id`, NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()` |
| archived | BOOLEAN | NOT NULL, default `false` |

### `releases`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(100) | UNIQUE, NOT NULL |
| target_date | DATE | nullable |
| status | ENUM('planned', 'in_progress', 'released') | NOT NULL, default `planned` |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |

### `test_runs`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| test_case_id | UUID | FK → `test_cases.id`, NOT NULL, indexed |
| release_id | UUID | FK → `releases.id`, NOT NULL, indexed |
| status | ENUM('passed', 'failed', 'blocked', 'skipped') | NOT NULL |
| source | ENUM('manual', 'automated') | NOT NULL, indexed |
| duration_ms | INTEGER | nullable (populated for automated runs) |
| logs | TEXT | nullable |
| executed_by | UUID | FK → `users.id`, nullable (null for automated CI runs) |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()`, indexed |

### `defects`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | NOT NULL |
| severity | ENUM('low', 'medium', 'high', 'critical') | NOT NULL |
| status | ENUM('open', 'triaged', 'fixed', 'verified', 'closed') | NOT NULL, default `open` |
| test_run_id | UUID | FK → `test_runs.id`, nullable |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |
| resolved_at | TIMESTAMPTZ | nullable |

### `evidence`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| test_run_id | UUID | FK → `test_runs.id`, NOT NULL |
| file_path | VARCHAR(500) | NOT NULL |
| file_type | VARCHAR(50) | NOT NULL (e.g., `image/png`, `text/plain`) |
| uploaded_at | TIMESTAMPTZ | NOT NULL, default `now()` |

*(Schema designed specifically for manual + automated test tracking per the project's domain, per template instructions)*

---

## Relationships

- `users` 1—N `test_cases` (created_by)
- `users` 1—N `test_runs` (executed_by, nullable for automated runs)
- `test_cases` 1—N `test_runs`
- `releases` 1—N `test_runs`
- `test_runs` 1—N `evidence`
- `test_runs` 1—0..1 `defects` (a failed run may generate at most one linked defect; a defect can also exist without a run)

---

## Indexing Strategy

| Table | Index | Rationale |
|---|---|---|
| `test_cases` | `module`, `archived` | Fast filtering on dashboard by module; exclude archived by default |
| `test_runs` | `test_case_id`, `release_id`, `source`, `created_at` | Core query paths: history per test case, per release, by source, chronological |
| `defects` | `status`, `severity` | Fast triage queue queries |
| `evidence` | `test_run_id` | Fast lookup of attachments per run |

## Migration Strategy

- Alembic manages all schema migrations; one migration per logical schema change.
- Enum types (`role`, `priority`, `status`, `source`, `severity`) are managed as native PostgreSQL enums in
  production, with SQLite fallback using `CHECK` constraints in dev via SQLAlchemy's cross-dialect enum handling.
- Migrations are run automatically in the Podman Compose startup sequence for dev, and as a discrete CI/CD
  step (`alembic upgrade head`) before deployment in production.

*(Indexing and migration approach tailored to expected query patterns of this project)*
