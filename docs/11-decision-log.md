# Decision Log

| Date | Decision | Rationale | Alternatives Considered | Outcome |
|---|---|---|---|---|
| 2026-07-11 | Build QualityHub on the FastAPI + HTMX + PostgreSQL template rather than a standalone SPA | Template already provides Auth, RBAC, structured logging, and CI/CD scaffolding; SSR+HTMX fits an internal tool's simplicity needs | React/Vue SPA with separate API; off-the-shelf test management SaaS (e.g., TestRail) | Adopted — template baseline used as-is |
| 2026-07-11 | Automation scripts (Selenium/TestNG/JUnit) integrate via REST API only, not as an in-repo dependency | Keeps QualityHub's stack (Python/FastAPI) decoupled from automation engineers' language/framework choices (some may use Java) | Embedding automation runners directly inside the FastAPI app | Adopted — API-only integration boundary |
| 2026-07-11 | Use pluggable AI provider (Mock → OpenAI → Anthropic) for test-case drafting and failure summarization | Reuses template's existing pattern; avoids vendor lock-in; Mock provider allows deterministic testing | Hardcoding a single LLM vendor | Adopted — `AI_PROVIDER` env var controls provider |
| 2026-07-11 | AI-generated test cases are drafts only, requiring human review before becoming "real" test cases | Mitigates risk of low-quality or hallucinated test steps entering the official suite unreviewed; addresses prompt-injection concerns raised in the security doc | Auto-publishing AI drafts directly | Adopted — draft-then-approve workflow |
| 2026-07-11 | Coverage/trend aggregates computed by an async background worker, not per-request | Avoids expensive recomputation on every dashboard page load as test run history grows | Real-time computation on each GET request | Adopted — background worker pattern |
| 2026-07-11 | Treat this as an internal tool with no external compliance mandate (GDPR/HIPAA) by default | No customer PII processed; used only by SecPod's internal QA team | Applying full compliance framework preemptively | Adopted, pending confirmation from SecPod's compliance team |

*(Decisions reflect the architectural and scoping choices made while filling this documentation set — adjust dates/rationale to match actual team discussions)*
