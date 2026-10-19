# Project Experience Library: Lessons & Architectural Insights

Documented lessons from system development, bug fixes, and operational milestones.

---

## EXP-001: Ingress Guardrail Regex Grammar (DAN and Roleplay Bypasses)
* **cue**: When designing regex-based ingress guardrails for prompt injection and jailbreak defense.
* **lesson**: Make leading articles optional (e.g., `(a\s+)?DAN`), support possessive pronouns for indirect overrides (`(your|my|the)\s+instructions`), and explicitly match privilege escalation verbs (`(sudo|admin|root)`).
* **evidence**: Initial evaluation scored 58% on `attack_corpus.jsonl` because 5 attack patterns bypassed naive regex; expanding pattern coverage drove injection defense to 100% across all 12 adversarial test cases.

---

## EXP-002: Deterministic Invariant Verifiers for Tabular Financial Math
* **cue**: When evaluating agent outputs involving financial calculations, waterfalls, or cap tables.
* **lesson**: Never use string exact match or qualitative LLM judges for tabular math; evaluate mathematical invariants directly (sum of payouts == exit valuation, payouts >= 0, liquidation preference seniority respected, positive MOIC).
* **evidence**: Waterfall eval scored 0% when comparing descriptive text fields, but passed 100% once converted to an invariant verification function (`_verify_waterfall()`), catching genuine arithmetic properties without brittle text formatting failures.

---

## EXP-003: Ephemeral vs. Persistent Cloud Hosting for Agent Demos
* **cue**: When providing public live links for user testing or demoing agent frontends.
* **lesson**: Ephemeral tunnels (e.g., `trycloudflare`) disconnect on host sleep or network renegotiation; provide a containerized Blueprint (`render.yaml`) with dynamic `${PORT:-8000}` binding for zero-cost 24/7 persistence.
* **evidence**: The trycloudflare tunnel dropped overnight (`curl code 6: Could not resolve host`) after the development laptop slept, requiring tunnel restart and prompting the Render deployment configuration.

---

## EXP-004: Python 3.10 CI Compatibility in Modern Python Development
* **cue**: When writing f-strings or typing constructs in a local environment newer than CI (e.g., Python 3.14 local vs 3.10 CI).
* **lesson**: Never use backslashes inside f-string expressions; use `.format()` or pre-compute variables outside the string.
* **evidence**: GitHub Actions CI failed on Python 3.10 with `SyntaxError: f-string expression cannot include a backslash` despite passing cleanly on local Python 3.14.

---

## EXP-005: Intent Classification Disambiguation for Generic Nouns
* **cue**: When routing user queries that mention shared domain entities (e.g., "data room").
* **lesson**: Gate entity nouns with explicit action verbs (e.g. `(request|need|upload).*(data\s*room)`) rather than bare keywords.
* **evidence**: The prompt "summarize risks in the data room" was misclassified as `DOCUMENT_REQUEST` instead of `DILIGENCE_QUERY` until the pattern was gated with action verbs, driving intent classification accuracy from 87% to 100%.
