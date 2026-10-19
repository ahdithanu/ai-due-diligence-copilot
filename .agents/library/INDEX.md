# Experience Library Index

Catalog of operational and architectural lessons learned during project evolution.

| ID | Topic | Component | Outcome |
| :--- | :--- | :--- | :--- |
| **EXP-001** | Ingress Guardrail Regex Grammar | `backend/services/intent_router.py` | Injection defense: 58% -> 100% |
| **EXP-002** | Deterministic Invariant Verifiers | `eval/run_eval.py` | Waterfall math eval: 0% -> 100% |
| **EXP-003** | Ephemeral vs Persistent Cloud Hosting | `render.yaml`, `Dockerfile.api` | 24/7 uptime without host sleep drops |
| **EXP-004** | Python 3.10 CI Compatibility | Global code formatting | Zero SyntaxError in CI pipeline |
| **EXP-005** | Intent Classification Action Gating | `backend/services/intent_router.py` | Intent classification: 87% -> 100% |

See `EXPERIENCE.md` for full `cue`, `lesson`, and `evidence` entries.
