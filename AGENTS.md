# AI Due Diligence Copilot: Agent Workspace Rules

## 1. Verified Workspace Facts & Mechanics

* **Python Runtime**: Use `.venv/bin/python` and `.venv/bin/pytest`. The local virtual environment runs Python 3.14, but CI runs Python 3.10.21.
* **Python 3.10 Invariant**: Never put backslashes inside f-string expressions (e.g. `{... \ ...}`). It causes `SyntaxError` in Python 3.10/3.11. Use `.format()` or pre-compute variables.
* **Testing Command**: Run tests with `PYTHONPATH=. .venv/bin/pytest tests/ -v`.
* **Git Operations**: Git commands modifying repo state require `BypassSandbox: true` because `.git/index.lock` is restricted in standard sandbox.
* **Frontend Build & Static Serving**: Frontend is built with `cd frontend && npm run build` (outputs to `frontend/dist`). FastAPI mounts `/assets` and serves `index.html` at `/`.
* **Database**: Local development uses SQLite at `diligence_copilot.db` in the workspace root.
* **CI Simulation**: Validate the complete release pipeline locally with `python scripts/verify_ci_pipeline.py`.
* **Demo Data**: Seed mock investment materials and documents with `python scripts/seed_demo_data.py`.

---

## 2. Skill Trigger Lines

* When evaluating agent accuracy, running regression tests, benchmarking guardrails, or testing retrieval and math, load the `eval-runner` skill.
* When building or deploying the application (Render, Docker, AWS, or local tunnels), load the `deploy-ops` skill.
* When preparing for executive, technical lead, or forward-deployed engineer interviews, load the `interview-prep` skill.

---

## 3. Core Architectural Invariants

* **Deterministic Math Separation**: Never ask LLMs to compute cap table waterfalls, equity payouts, or IRR directly. Extract structured parameters and delegate calculation to `backend/services/waterfall_calculator.py`.
* **Ingress Guardrail Defense**: User queries must pass through `validate_ingress_guardrails()` in `backend/services/intent_router.py` before hitting LLM inference.
* **Source Grounding**: All diligence answers must include verifiable chunk ID citations (`rag-chunk-X`, document name, and page number).
