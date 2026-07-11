# Risk Analysis

## Risk Register

| Risk | Likelihood | Impact | Mitigation Strategy |
|---|---|---|---|
| Automation engineers can't easily integrate existing Selenium/TestNG/JUnit suites with the REST ingestion API, requiring extra adapter work | Medium | High | Validate integration feasibility early with a spike/prototype before full FR-004 implementation; budget time for a lightweight reporter plugin if needed |
| Success-criteria targets (e.g., 30% regression time reduction) are unrealistic or unmeasured against a real baseline | Medium | Medium | Gather actual current-state QA metrics before committing to targets; treat initial numbers as placeholders pending validation |
| Low adoption — QA engineers continue using spreadsheets/ad-hoc scripts instead of QualityHub | Medium | High | Prioritize the manual test execution UI's ease-of-use; involve QA engineers in early UX feedback; make automated ingestion frictionless to encourage automatic buy-in |
| AI-drafted test cases are low quality or misleading if reviewed carelessly | Low–Medium | Medium | Enforce draft-then-approve workflow (already decided); train QA team that AI output is a starting point, not a final artifact |
| Defect records referencing unpatched security issues in SecPod's own product are exposed to unauthorized users | Low | Critical | Strict RBAC enforcement, audit logging on defect access/status changes, treat as "Internal — sensitive" per data classification |
| CI service tokens leak (e.g., committed to a public repo, logged) | Low | High | Scoped, revocable tokens stored only as CI secrets; automated secret-scanning in CI; tokens never written to logs |
| Database growth (test run history) degrades dashboard/query performance over time | Medium | Medium | Indexing strategy already defined in `docs/06-database-design.md`; monitor and consider partitioning if `test_runs` exceeds ~10M rows |
| AI provider outage blocks core QA workflows | Low | Low | AI features designed to fail gracefully (NFR-011) without blocking manual/automated test tracking, which remain the core function |
| Scope creep — team requests unbounded feature additions before v1.0 core is stable | Medium | Medium | Roadmap explicitly separates v1.0/v1.1/v2.0; new requests routed to v1.1+ unless critical to core test tracking |
| Team lacks bandwidth to build both the platform and continue day-to-day QA responsibilities | Medium | High | Phase rollout — start with a minimal v1.0 subset (test case management + manual execution) before automated ingestion and AI features |

*(Risks focused on QualityHub's specific domain — automation integration, security-sensitive defect data, and internal adoption — per template instructions)*
