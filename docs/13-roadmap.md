# Roadmap

## Version 1.0 — Core Platform (Template-Derived Foundation)

- [x] User Authentication (JWT + bcrypt + RBAC) — carried over from template baseline
- [ ] Test Case Management (CRUD, tagging, search)
- [ ] Manual Test Execution flow (step-by-step, pass/fail/blocked)
- [ ] Automated Result Ingestion API (CI service-token auth)
- [ ] Defect Linking & Status Tracking
- [ ] Coverage & Trends Dashboard
- [ ] Evidence Upload (screenshots/logs)
- [ ] Podman Compose local dev + basic GitHub Actions CI

*(Reflects the "Must Have" functional requirements from `docs/02-requirements.md`)*

---

## Version 1.1 — Near-Term Enhancements

- [ ] AI-Assisted Test Case Drafting (requirement text → draft test case)
- [ ] AI Failure-Pattern Summarization across releases
- [ ] Release Readiness View (coverage % + open defects snapshot)
- [ ] Test Suite Export/Import (CSV/JSON)
- [ ] Rate limiting hardening on auth and ingestion endpoints
- [ ] Structured audit log for defect status transitions

*(Reflects the "Should Have"/"Could Have" requirements plus near-term security hardening)*

---

## Version 2.0 — Long-Term Vision

- [ ] Direct integrations with common CI providers (GitHub Actions, Jenkins) beyond the generic API — e.g.,
      a GitHub Action that auto-posts results without custom scripting
- [ ] Automated flaky-test detection (statistical analysis of intermittent pass/fail patterns per test case)
- [ ] Performance/load testing module extending beyond functional test tracking
- [ ] Cross-project support — if SecPod's QA team grows to cover multiple product lines beyond the current
      unified platform, extend QualityHub to multi-project workspaces
- [ ] Deeper AI capabilities: auto-suggesting which existing test cases are impacted by a given code diff
- [ ] Public-facing release notes generator derived from resolved defects (if ever needed externally)

*(Long-term items speculative and dependent on team growth/adoption — adjust based on actual future priorities)*
