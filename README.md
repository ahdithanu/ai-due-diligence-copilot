# AI Investment Due Diligence Copilot

An evidence-grounded institutional investment analysis platform powered by state-machine graph agent orchestration, explicit typed state, conditional routing, critic-evaluator loops, human-in-the-loop gates, and deterministic financial calculations.

---

## Executive Overview & Problem Statement

Generic Retrieval-Augmented Generation (RAG) chatbots and simple agent chains are fundamentally insufficient for institutional venture capital and private equity due diligence. Standard LLM chatbots suffer from:
1. **Unchecked Hallucinations & Math Errors**: Asking an LLM to compute financial ratios (ARR, NRR, LTV/CAC, Rule of 40) directly in text yields inconsistent, unverified arithmetic.
2. **Linear Bias & Lack of Cross-Examination**: Fixed sequential prompt chains blindly pass unverified claims forward without checking for inter-document contradictions (e.g., pitch deck ARR vs. audited P&L).
3. **Black-Box Reasoning**: Traditional agents overwrite intermediate state, concealing why a recommendation was made and rendering claims un-auditable.

The **AI Investment Due Diligence Copilot** resolves these limitations through **Graph Engineering**:
- **Persistent Shared State (`DiligenceState`)**: An immutable, strictly typed Pydantic state snapshot that travels through all nodes, preserving full revision lineage and execution history.
- **Deterministic Financial Engine**: Computes 17 core financial and unit economic metrics programmatically in Python AST with exact formula logging and confidence tracking before LLM reasoning occurs.
- **Looped Analyst-Critic-Evaluator Architecture**: Every specialist domain (Financial, Market, Competitive, Customer, Product, Risk, Unit Economics) operates in an iterative Generate $\rightarrow$ Critique $\rightarrow$ Judge $\rightarrow$ Revise cycle until strict quality thresholds are satisfied.
- **Adversarial Investment Committee Debate**: Bull, Bear, and Skeptic nodes debate opposing cases using evidence quality and materiality weighting—with Skeptic nodes capable of routing execution backward if critical gaps remain.
- **Evidence Provenance Graph**: Maps every material claim directly to source document chunks with strict taxonomy (`FACT`, `CALCULATION`, `INFERENCE`, `ASSUMPTION`, `UNRESOLVED_QUESTION`).
- **Human-in-the-Loop Gates**: Interrupts execution automatically upon detecting material financial contradictions, low confidence recommendations ($< 0.60$), missing critical periods, or max loop iterations (3 iterations).

---

## Graph System Architecture

```
                                  [Document Upload]
                                          |
                                          v
                                  (Ingestion Node)
                                          |
                                          v
                               (Document Parser Node)
                                          |
                                          v
                               (Evidence Extractor Node)
                                          |
                                          v
                         (Deterministic Financial Engine Node)
                                          |
                                          v
                 +-------------------------------------------------+
                 |            Specialist Analyst Nodes             |
                 | (Financial, Market, Competitive, Customer,      |
                 |         Product, Risk, Unit Economics)          |
                 +------------------------+------------------------+
                                          |
                                          v
                               (Critic Evaluator Node)
                                          |
                             [Pass?] -----+----- [Fail & Iter < 3]
                                |                       |
                                v                       v
                      (Cross Examiner Node)      (Analyst Revision)
                                |
                                v
                       (Gap Detector Node)
                                |
                                v
                 +-------------------------------------------------+
                 |           Investment Committee Stage            |
                 |           (Bull Node vs. Bear Node)             |
                 +------------------------+------------------------+
                                          |
                                          v
                                   (Skeptic Node)
                                          |
                        [Critical Flaws?] + ----- [Sufficient Evidence]
                                |                       |
                                v                       v
                      (Human Review Gate)       (IC Synthesizer Node)
                                |                       |
                         [User Action]                  v
                                |              (Memo Generator Node)
                                v                       |
                      (Resumed Execution)               v
                                                [Final Institutional Memo]
```

---

## State Schema & Provenance Taxonomy

The shared graph state (`DiligenceState`) is defined via strict Pydantic v2 schemas:

### Claim Taxonomy
- **`FACT`**: Verbatim or trivially extracted primary source document evidence.
- **`CALCULATION`**: Programmatically computed metric using deterministic Python formulas.
- **`INFERENCE`**: Logical deduction derived by an analyst node anchored in facts/calculations.
- **`ASSUMPTION`**: Working premise required for modeling where primary evidence is absent.
- **`UNRESOLVED_QUESTION`**: Material gap or contradiction identified during cross-examination.

### Graph State Components
- `investment_id`, `company_name`, `industry`, `target_round`, `check_size_usd`
- `documents`, `document_chunks`, `evidence_records`
- `financial_metrics` (ARR, NRR, LTV/CAC, Rule of 40, Gross Margin, Burn, Runway, etc.)
- `specialist_analyses` (Financial, Market, Competitive, Customer, Product, Risk, Unit Economics)
- `risk_register`, `contradictions`, `open_questions`, `assumptions`
- `bull_case`, `bear_case`, `skeptic_critique`, `investment_thesis`
- `recommendation` (`INVEST`, `PASS`, `CONDITIONAL_PASS`), `confidence_score`
- `memo_markdown`, `evaluations`, `iteration_counts`, `execution_history`

---

## Core Specialist & Graph Nodes

1. **DeterministicFinancialEngineNode**: Computes 17 financial & unit economic metrics in code.
2. **FinancialAnalystNode**: Consumes metrics & evidence to build financial assessment.
3. **MarketAnalystNode**: Evaluates TAM/SAM/SOM, CAGR, and macro market tailwinds.
4. **CompetitiveAnalystNode**: Evaluates competitive moats, direct/indirect rivals, and positioning.
5. **CustomerAnalystNode**: Evaluates ACV, churn, NRR, NPS, and customer concentration risk.
6. **ProductAnalystNode**: Evaluates tech stack, IP/patents, roadmap maturity, and technical debt.
7. **RiskAnalystNode**: Identifies key person, regulatory, market, and burn risks $\rightarrow$ populates `risk_register`.
8. **UnitEconomicsAnalystNode**: Evaluates CAC, LTV, LTV/CAC payback, and unit margins.
9. **CriticEvaluatorNode**: Attacks reasoning, missing evidence, bad math, or excessive optimism/pessimism.
10. **CrossExaminerNode**: Detects inter-specialist & document contradictions (e.g. pitch deck vs. audited statements).
11. **GapDetectorNode**: Converts missing evidence and risks into ranked, actionable `DiligenceQuestion`s.
12. **BullNode**: Builds the strongest evidence-backed upside case.
13. **BearNode**: Builds the strongest evidence-backed downside case.
14. **SkepticNode**: Attacks both Bull and Bear cases for ungrounded assumptions or bias.
15. **ICSynthesizerNode**: Synthesizes Bull/Bear/Skeptic positions using evidence quality and materiality weighting.
16. **MemoGeneratorNode**: Synthesizes a 20-section institutional investment memo with popover evidence citations.
17. **HumanReviewGateNode**: Intercepts execution when critical flags or max iterations occur.

---

## Deterministic Financial Metric Formulas

| Metric Name | Formula | Unit |
|---|---|---|
| **YoY Revenue Growth** | $\frac{\text{Revenue}_t - \text{Revenue}_{t-1}}{\text{Revenue}_{t-1}} \times 100$ | Percentage (%) |
| **Gross Margin** | $\frac{\text{Revenue} - \text{COGS}}{\text{Revenue}} \times 100$ | Percentage (%) |
| **Operating Margin** | $\frac{\text{Operating Income}}{\text{Revenue}} \times 100$ | Percentage (%) |
| **EBITDA Margin** | $\frac{\text{EBITDA}}{\text{Revenue}} \times 100$ | Percentage (%) |
| **Burn Rate** | $\text{Cash}_{t-1} - \text{Cash}_t$ | USD / Month |
| **Runway** | $\frac{\text{Cash Balance}}{\text{Monthly Burn Rate}}$ | Months |
| **ARR** | $\text{MRR} \times 12$ | USD |
| **Net Revenue Retention (NRR)** | $\frac{\text{ARR}_{\text{end}} - \text{ARR}_{\text{new}}}{\text{ARR}_{\text{start}}} \times 100$ | Percentage (%) |
| **Customer Concentration** | $\frac{\text{Top 5 Customer Revenue}}{\text{Total Revenue}} \times 100$ | Percentage (%) |
| **CAC** | $\frac{\text{Sales \& Marketing Spend}}{\text{New Customers Acquired}}$ | USD |
| **LTV** | $\frac{\text{ARPU} \times \text{Gross Margin \%}}{\text{Customer Churn Rate}}$ | USD |
| **LTV / CAC Ratio** | $\frac{\text{LTV}}{\text{CAC}}$ | Ratio |
| **CAC Payback** | $\frac{\text{CAC}}{\text{ARPU} \times \text{Gross Margin \%}}$ | Months |
| **Rule of 40** | $\text{YoY Revenue Growth \%} + \text{EBITDA Margin \%}$ | Ratio |

---

## Tech Stack & Architecture

- **Backend Framework**: Python 3.10+, FastAPI
- **Database Layer**: SQLAlchemy 2.0 (Async), SQLite / PostgreSQL, Alembic
- **Graph Orchestration**: Custom Async State Machine (`GraphEngine`) supporting conditional edges, loop state retention, and DB snapshot persistence
- **Frontend Layer**: React 18, TypeScript, Vite, Vanilla CSS (Dark Mode, Glassmorphism, Micro-animations)
- **Testing**: `pytest`, `pytest-asyncio`, `httpx` (49 unit, integration, and adversarial tests passing)

---

## Setup & Execution Guide

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Backend Setup & Test Suite
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (or use uv)
pip install -e .

# Run complete backend test suite (49 tests)
PYTHONPATH=. pytest -v

# Start FastAPI server
uvicorn backend.main:app --reload --port 8000
```

FastAPI OpenAPI documentation available at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Build production bundle
npm run build

# Start Vite dev server
npm run dev
```

Frontend application available at: `http://localhost:5173`

---

## Portfolio & Engineering Artifact Highlights

- **Graph Execution Visualizer**: Interactive DAG UI component displaying active execution state, iteration counters, critic evaluation sub-scores, and human review pauses.
- **Evidence Provenance Explorer**: Interactive document chunk viewer linking extracted claims and metrics back to source page numbers and section headers.
- **Adversarial Test Suite (`tests/test_adversarial_diligence.py`)**: Tests system behavior under conflicting pitch deck vs. audited statements, missing financial periods, bad math citations, and max iteration loop fallbacks.
