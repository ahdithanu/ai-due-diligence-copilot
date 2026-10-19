---
name: eval-runner
description: Run, evaluate, and benchmark agent capabilities across guardrails, intent routing, RAG retrieval, and waterfall math using the golden dataset suite.
---

# Eval Runner Skill

Use this skill when running regressions, evaluating guardrail robustness, benchmarking retrieval accuracy, or adding new golden test cases.

## Core Execution Commands

Run all 6 tasks (56 golden samples):
```bash
PYTHONPATH=. .venv/bin/python eval/run_eval.py --all
```

Run a specific task:
```bash
PYTHONPATH=. .venv/bin/python eval/run_eval.py --task injection_defense
PYTHONPATH=. .venv/bin/python eval/run_eval.py --task intent_classification
PYTHONPATH=. .venv/bin/python eval/run_eval.py --task rag_retrieval
PYTHONPATH=. .venv/bin/python eval/run_eval.py --task waterfall_math
PYTHONPATH=. .venv/bin/python eval/run_eval.py --task dlp_redaction
PYTHONPATH=. .venv/bin/python eval/run_eval.py --task groundedness
```

Run the automated pytest eval harness:
```bash
PYTHONPATH=. .venv/bin/pytest tests/test_eval_framework.py -v
```

## Adding Golden Samples

When adding new evaluation cases, update the corresponding JSONL dataset under `eval/datasets/`:
* `attack_corpus.jsonl`: Ingress prompt injections, jailbreaks, and evasions.
* `intent_routing.jsonl`: Query intent classifications (`DILIGENCE_QUERY`, `FINANCIAL_DEEPDIVE`, `CAP_TABLE_WATERFALL`, `DOCUMENT_REQUEST`, `OUT_OF_SCOPE`).
* `golden_queries.jsonl`: Expected RAG chunk IDs and minimum recall thresholds.
* `waterfall_scenarios.jsonl`: Cap table structures and exit valuations.
* `dlp_samples.jsonl`: PII / PCI redaction expectations.
* `groundedness_samples.jsonl`: Grounded answers with source citations.

## Key Invariant Rules

1. **Deterministic Invariant Checks for Math**: For waterfall calculations, verify mathematical invariants (capital conservation, non-negative payouts, liquidation preference ordering) rather than exact text strings.
2. **Schema Field Names**: `RAGSearchResult` uses the `id` field (not `chunk_id`). Always access `result.id`.
