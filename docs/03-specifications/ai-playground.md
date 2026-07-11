# Specification: AI Playground

## Purpose
Defines the behavior of QualityHub's AI Playground module, which repurposes the template's pluggable AI/LLM
feature into two QA-specific capabilities: test-case drafting and failure-pattern summarization.

## Scope
Covers `/api/v1/ai/draft-test-case`, `/api/v1/ai/summarize-failures`, and the `/ai` dashboard views.

---

## Provider Configuration

| Behavior | Detail |
|---|---|
| Provider selection | Controlled via `AI_PROVIDER` env var: `mock` (default, no API key, deterministic output for dev/test) → `openai` → `anthropic` |
| Provider abstraction | `AIService` wraps provider-specific calls behind a single interface so switching providers requires no changes to endpoints or UI |
| Caching | Responses cached in Redis keyed by request content hash, to avoid redundant LLM calls for repeated/identical requests |

*(Reuses the template's pluggable AI pattern as-is per template instructions)*

---

## Feature: AI Test-Case Drafting

| Behavior | Detail |
|---|---|
| Input | Plain-language requirement description (free text, max 2000 characters) |
| Output | Structured JSON: ordered draft steps + a draft expected result |
| Review gate | Draft is never auto-saved as a real `TestCase` — the user must review, optionally edit, and explicitly click "Save as Test Case" |
| Rationale | Mitigates risk of low-quality or hallucinated test steps entering the official suite unreviewed, and reduces exposure to prompt-injection style manipulation of the AI provider |
| UI flow | Requirement text submitted via `hx-post`; loading indicator swaps to the draft result partial once the response returns |

## Feature: AI Failure-Pattern Summarization

| Behavior | Detail |
|---|---|
| Input | `release_id` + optional `limit` (number of recent automated runs considered, default 50) |
| Output | Free-text summary + a list of identified failure "themes" (e.g., recurring timeout errors in a specific module) |
| Data boundary | Only reads `status=failed` test runs and their associated logs for the specified release; does not cross into other releases' data |
| Use case | Helps QA Leads quickly spot systemic issues across many automated failures without manually reading every log |

---

## Guardrails

- AI-generated content (drafts, summaries) is always presented as a suggestion, never automatically applied to
  test cases, defect records, or release status.
- Requirement text and log content sent to the AI provider are treated as "Internal" per the data sensitivity
  classification in `docs/08-security.md`. The choice of production provider (`openai` vs. `anthropic`) should
  be confirmed against SecPod's data-handling policy before enabling either in production.
- If the AI provider is unreachable or errors out, both endpoints fail gracefully (clear error message) without
  affecting core test management functionality (NFR-011).

## Error Handling

| Condition | Response |
|---|---|
| AI provider unreachable/timeout | `503 Service Unavailable` with a clear message; core app unaffected |
| Requirement text exceeds length limit | `422 Unprocessable Entity` |
| Invalid/nonexistent `release_id` | `404 Not Found` |

*(Generated based on FR-007/FR-008 in `docs/02-requirements.md`, the AI Endpoints in `docs/05-api-design.md`, and the AI/LLM row in `docs/00-project-overview.md`)*
