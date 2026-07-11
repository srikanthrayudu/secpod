# Specification: Dashboard

## Purpose
Defines the behavior of QualityHub's main dashboard and admin views — the primary landing experience for QA
Engineers, QA Leads, and Admins.

## Scope
Covers the home dashboard (`/`), coverage/trends views, release readiness view, and admin user-management
views. Does not cover the test execution flow itself (see Test Execution spec) or the AI Playground UI
(see AI Playground spec).

---

## Home Dashboard (`/`)

| Section | Behavior |
|---|---|
| Coverage summary cards | Show test coverage % by module, computed from the latest background-worker aggregate (not real-time per-request) |
| Recent activity feed | Lists the most recent test runs (manual and automated) across all releases, newest first |
| Open defects widget | Shows count of `Open`/`Triaged` defects, with `critical` severity ones highlighted distinctly |
| Drill-down | Clicking a coverage card loads a per-module breakdown via an HTMX partial, without a full page navigation |

## Coverage & Trends View (`/dashboard/coverage`)

| Section | Behavior |
|---|---|
| Filters | By release, module, and date range |
| Pass/fail trend chart | Trend of pass rate over time for the selected release/module |
| Coverage table | Test cases vs. cases with at least one recorded run, broken down by module |
| Source breakdown | Split of manual vs. automated run counts, to track automation adoption progress (per success criteria in `docs/01-business-problem.md`) |

## Release Readiness View (`/releases/{id}/readiness`)

| Section | Behavior |
|---|---|
| Snapshot | Coverage %, pass rate, and open defect count for the selected release, loaded via `hx-trigger="load"` so the page shell renders instantly while data loads asynchronously |
| Blockers | Any `critical`-severity open defect linked to the release is flagged as a release blocker |

## Admin — User Management View (`/admin/users`)

*(Admin Dashboard functionality carried over from the template baseline, scoped to QualityHub's user roles)*

| Behavior | Detail |
|---|---|
| List/search users | Admin can list, search, and filter users by role or status |
| Edit role | Admin can change a user's role among `qa_engineer` / `qa_lead` / `admin` |
| Deactivate/reactivate | Admin can deactivate a user (blocks login) without deleting their historical test run/defect records |
| Delete | Restricted — deleting a user is discouraged in favor of deactivation, to preserve `executed_by`/`created_by` audit trails |

---

## Non-Functional Notes

- All dashboard views are server-rendered (Jinja2) with HTMX partial updates for filters and drill-downs,
  consistent with the SSR + HTMX approach in `docs/07-ui-ux.md`.
- Coverage/trend data is precomputed by the async background worker (`coverage_worker`) rather than calculated
  per request, to keep dashboard load times under the NFR-003 target (< 2s for up to 5,000 test cases).
- Access to `/admin/*` views is restricted to the `admin` role; `qa_lead` can view coverage/readiness views but
  not user management.

*(Generated based on FR-006/FR-009 in `docs/02-requirements.md`, the template's built-in Admin Dashboard feature, and the HTMX interaction model in `docs/07-ui-ux.md`)*
