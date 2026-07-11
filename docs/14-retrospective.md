# Retrospective

## Development Context & Setup Challenges

QualityHub was scoped and documented starting from the Startup & Hackathon Template's fixed tech stack
(FastAPI + HTMX + PostgreSQL + SQLAlchemy 2.0 async + JWT/bcrypt auth), adapted to SecPod QA team's specific
need for a centralized test management and automation-reporting platform. Since implementation has not yet
begun, this retrospective reflects the planning/documentation phase rather than a completed development cycle.

Anticipated setup challenges to watch for once implementation starts:

- **Reconciling manual vs. automated data models** — designing a single `TestRun` table to serve both
  human-driven and CI-driven submissions cleanly (different fields are meaningful for each: `executed_by` vs.
  `duration_ms`/`logs`) required care to avoid an overly generic, hard-to-query schema.
- **CI service-token strategy** — deciding how automation pipelines (potentially written in Java via TestNG/JUnit,
  not just Python) authenticate to the API needed a decision separate from user-facing JWT auth (see decision log).
- **Scoping AI features responsibly** — ensuring AI-drafted test cases remain review-gated rather than
  auto-published required an explicit workflow decision early, before any implementation began.

*(Since this is pre-implementation, challenges are anticipated based on design decisions made so far — revisit and update once real development begins)*

---

## What Went Well

- Reusing the template's existing Auth, layered architecture, and CI/CD scaffolding significantly reduced the
  number of net-new architectural decisions needed — most effort went into domain modeling (test cases, runs,
  defects) rather than infrastructure.
- The pluggable AI provider pattern from the template mapped cleanly onto two genuinely useful QA features
  (test-case drafting, failure summarization) without requiring new integration work.
- Documenting the API-first integration boundary for automation tooling early (rather than after some scripts
  were already built) should avoid rework later.

*(Reflects the documentation/planning phase — update with real retrospective notes after the first development sprint)*

---

## Key Learnings & Improvements for This Project

- Confirm with SecPod's actual QA/automation engineers **before** implementation whether TestNG/JUnit results
  can be adapted to POST JSON to the ingestion API directly, or whether a small adapter/reporter plugin needs
  to be built for each framework — this affects FR-004's real-world feasibility.
- Validate the assumed success-criteria numbers in `docs/01-business-problem.md` (e.g., 30% regression time
  reduction) against SecPod's actual current baseline metrics once available, rather than treating them as fixed targets.
- Revisit data retention and internal compliance questions (flagged as open in `docs/08-security.md`) with
  SecPod's compliance/security stakeholders before production rollout.

*(Learnings framed as open items to validate before/during implementation, since no development has occurred yet)*
