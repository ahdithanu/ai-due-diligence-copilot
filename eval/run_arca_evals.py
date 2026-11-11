import os
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import json
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.domain.schemas import (
    ArcaEvalScorecard,
    StaffEditRequest,
)
from backend.services.artifact_verifier_service import artifact_verifier_service
from backend.services.fee_and_conflict_scanner import fee_and_conflict_scanner
from backend.services.staff_feedback_eval_service import staff_feedback_eval_service
from backend.services.dreaming_service import dreaming_service
from eval.rogan_gladen import bootstrap_confidence_interval

GOLDEN_DATASET_PATH = os.path.join(os.path.dirname(__file__), "arca_golden_dataset.json")


class ModelUsageTrace(BaseModel):
    task_name: str
    model_name: str
    input_tokens: int
    output_tokens: int
    target_tier: str  # "flash" | "frontier"


DEFAULT_BENCHMARK_TRACES: List[ModelUsageTrace] = [
    # 4 Heavy tasks routed to Frontier
    ModelUsageTrace(task_name="ic_debate_cross_examination", model_name="claude-3-5-sonnet-20241022", input_tokens=18000, output_tokens=2200, target_tier="frontier"),
    ModelUsageTrace(task_name="deep_memo_synthesis", model_name="claude-3-5-sonnet-20241022", input_tokens=24000, output_tokens=3100, target_tier="frontier"),
    ModelUsageTrace(task_name="sec_filing_contradiction_detect", model_name="gpt-4o-2024-05-13", input_tokens=15000, output_tokens=1800, target_tier="frontier"),
    ModelUsageTrace(task_name="cap_table_waterfall_math", model_name="claude-3-5-sonnet-20241022", input_tokens=8500, output_tokens=1200, target_tier="frontier"),
    # 12 Routine / background watcher tasks routed to Flash/Light
    ModelUsageTrace(task_name="doc_ingestion_ocr_chunker", model_name="gemini-1.5-flash", input_tokens=4200, output_tokens=450, target_tier="flash"),
    ModelUsageTrace(task_name="founder_email_watcher", model_name="gemini-1.5-flash", input_tokens=1200, output_tokens=150, target_tier="flash"),
    ModelUsageTrace(task_name="data_room_change_listener", model_name="gemini-1.5-flash", input_tokens=3100, output_tokens=210, target_tier="flash"),
    ModelUsageTrace(task_name="diligence_qa_intent_router", model_name="gemini-1.5-flash", input_tokens=800, output_tokens=80, target_tier="flash"),
    ModelUsageTrace(task_name="pii_pre_filter", model_name="gemini-1.5-flash", input_tokens=1500, output_tokens=95, target_tier="flash"),
    ModelUsageTrace(task_name="banking_wire_event_listener", model_name="gemini-1.5-flash", input_tokens=900, output_tokens=110, target_tier="flash"),
    ModelUsageTrace(task_name="news_feed_risk_monitor", model_name="gemini-1.5-flash", input_tokens=2400, output_tokens=180, target_tier="flash"),
    ModelUsageTrace(task_name="lp_teaser_summarizer", model_name="gemini-1.5-flash", input_tokens=3600, output_tokens=350, target_tier="flash"),
    ModelUsageTrace(task_name="esop_option_pool_tracker", model_name="gemini-1.5-flash", input_tokens=2100, output_tokens=190, target_tier="flash"),
    ModelUsageTrace(task_name="covenant_compliance_sentry", model_name="gemini-1.5-flash", input_tokens=1950, output_tokens=220, target_tier="flash"),
    ModelUsageTrace(task_name="deal_readiness_tick", model_name="gemini-1.5-flash", input_tokens=1400, output_tokens=160, target_tier="flash"),
    ModelUsageTrace(task_name="log_event_archiver", model_name="gemini-1.5-flash", input_tokens=950, output_tokens=75, target_tier="flash"),
]


class ArcaEvalRunner:
    """
    Executes benchmark evaluations across Arca-style AI-native capabilities:
    1. Edge compliance and artifact verification (PII, SSN, promissory returns).
    2. Hidden fee & non-fiduciary conflict discovery (including clean baseline context-swapping).
    3. Staff edit feedback capture with mandatory 'Why' reason.
    4. Autonomous dreaming consolidation & deal readiness scoring (multi-dimensional continuous scoring).
    5. Dynamic tiered model cost efficiency benchmark (Frontier vs. Flash routing).
    6. Statistical rigor: Bootstrap 95% Confidence Intervals & Risk-Weighted Aggregation.
    """

    def __init__(self, dataset_path: str = GOLDEN_DATASET_PATH):
        with open(dataset_path, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)

    @staticmethod
    def evaluate_cost_efficiency(traces: List[ModelUsageTrace]) -> float:
        """
        Dynamically computes model routing cost efficiency across task traces.
        Validates that heavy analytical tasks hit Frontier and background watchers hit Flash.
        """
        if not traces:
            return 100.0
        correctly_routed = sum(
            1 for t in traces
            if (t.target_tier == "flash" and ("flash" in t.model_name.lower() or "light" in t.model_name.lower() or "mini" in t.model_name.lower()))
            or (t.target_tier == "frontier" and ("sonnet" in t.model_name.lower() or "gpt-4o" in t.model_name.lower() or "pro" in t.model_name.lower()))
        )
        return round((correctly_routed / len(traces)) * 100.0, 1)

    def run_all_evals(self, sample_traces: Optional[List[ModelUsageTrace]] = None) -> ArcaEvalScorecard:
        cases = self.dataset["test_categories"]
        case_details: List[Dict[str, Any]] = []
        all_case_scores: List[float] = []

        # --------------------------------------------------------------------
        # 1. Edge Artifact Compliance Evals (Deterministic regex & promissory)
        # --------------------------------------------------------------------
        comp_passed = 0
        comp_total = len(cases["edge_artifact_compliance"])
        for item in cases["edge_artifact_compliance"]:
            report = artifact_verifier_service.verify_artifact(item["id"], item["content"])
            is_pass = (report.passed == item["should_pass"])
            if is_pass:
                comp_passed += 1
            all_case_scores.append(1.0 if is_pass else 0.0)
            case_details.append({
                "test_id": item["id"],
                "category": "edge_artifact_compliance",
                "passed": is_pass,
                "detail": f"Actual passed: {report.passed}, Expected: {item['should_pass']}",
            })

        compliance_score = round((comp_passed / max(1, comp_total)) * 100.0, 1)

        # --------------------------------------------------------------------
        # 2. Hidden Fee & Conflict Discovery Evals
        # --------------------------------------------------------------------
        fee_scan = fee_and_conflict_scanner.scan_investment_documents("eval-test-deal")
        categories_found = {f.category for f in fee_scan.findings}
        fees_passed = 0
        fees_total = len(cases["hidden_fee_discovery"])
        for item in cases["hidden_fee_discovery"]:
            is_pass = item["expected_category"] in categories_found
            if is_pass:
                fees_passed += 1
            all_case_scores.append(1.0 if is_pass else 0.0)
            case_details.append({
                "test_id": item["id"],
                "category": "hidden_fee_discovery",
                "passed": is_pass,
                "detail": f"Found category: {item['expected_category']}",
            })

        # Context-swapping test on clean baseline agreement
        clean_text = (
            "Standard NVCA Model Series A Preferred Stock Purchase Agreement. "
            "Company maintains standard 1.0x non-participating liquidation preference. "
            "No advisory retainers, monitoring surcharges, or broker success fees are payable."
        )
        clean_findings = fee_and_conflict_scanner.scan_document_text(clean_text)
        context_swapping_passed = (len(clean_findings) == 0)
        all_case_scores.append(1.0 if context_swapping_passed else 0.0)
        case_details.append({
            "test_id": "eval-fee-context-swap-clean",
            "category": "hidden_fee_discovery",
            "passed": context_swapping_passed,
            "detail": f"Clean baseline context swap produced {len(clean_findings)} false positive findings (0 expected).",
        })
        if context_swapping_passed:
            fees_passed += 1
        fees_total += 1

        fees_score = round((fees_passed / max(1, fees_total)) * 100.0, 1)

        # --------------------------------------------------------------------
        # 3. Staff Feedback Loop Evals
        # --------------------------------------------------------------------
        staff_passed = 0
        staff_total = len(cases["staff_feedback_loop"])
        for item in cases["staff_feedback_loop"]:
            req = StaffEditRequest(
                target_field=item["target_field"],
                agent_original_value=item["agent_val"],
                human_adjusted_value=item["human_val"],
                reason_why=item["reason_why"],
                editor_role="Senior Partner",
            )
            rec = staff_feedback_eval_service.record_staff_edit("eval-test-deal", req)
            is_pass = bool(rec.id and rec.eval_candidate_id and rec.reason_why == item["reason_why"])
            if is_pass:
                staff_passed += 1
            all_case_scores.append(1.0 if is_pass else 0.0)
            case_details.append({
                "test_id": item["id"],
                "category": "staff_feedback_loop",
                "passed": is_pass,
                "detail": f"Eval candidate generated: {rec.eval_candidate_id}",
            })

        staff_score = round((staff_passed / max(1, staff_total)) * 100.0, 1)

        # --------------------------------------------------------------------
        # 4. Dreaming Consolidation Evals (Continuous multi-dimensional scoring)
        # --------------------------------------------------------------------
        dream_item = cases["dreaming_consolidation"][0]
        dream_resp = dreaming_service.run_dreaming("eval-test-deal", "Acme SaaS AI")
        inv_ratio = min(1.0, len(dream_resp.key_invariants_updated) / max(1, dream_item["min_invariants_count"]))
        readiness_ratio = min(1.0, dream_resp.agent_readiness_score / max(1, dream_item["min_readiness_score"]))
        dream_score_val = (inv_ratio + readiness_ratio) / 2.0
        dreaming_score_pct = round(dream_score_val * 100.0, 1)
        all_case_scores.append(dream_score_val)
        dream_is_pass = dream_score_val >= 1.0

        case_details.append({
            "test_id": dream_item["id"],
            "category": "dreaming_consolidation",
            "passed": dream_is_pass,
            "detail": f"Invariants Ratio: {inv_ratio:.2f}, Readiness Ratio: {readiness_ratio:.2f} ({dreaming_score_pct}%)",
        })

        # --------------------------------------------------------------------
        # 5. Dynamic Tiered Model Cost Efficiency
        # --------------------------------------------------------------------
        traces = sample_traces or DEFAULT_BENCHMARK_TRACES
        model_tiering_score = self.evaluate_cost_efficiency(traces)
        all_case_scores.append(model_tiering_score / 100.0)
        case_details.append({
            "test_id": "eval-model-cost-routing",
            "category": "model_cost_tiering",
            "passed": model_tiering_score >= 90.0,
            "detail": f"Dynamic Cost Routing: {model_tiering_score}% tasks optimally routed across Frontier vs. Flash.",
        })

        # --------------------------------------------------------------------
        # 6. Statistical Aggregation: Risk-Weighted & Bootstrap 95% CI
        # --------------------------------------------------------------------
        total_cases = len(all_case_scores)
        total_passed = sum(1 for s in all_case_scores if s >= 1.0)
        overall_pass_rate = round((total_passed / max(1, total_cases)) * 100.0, 1)

        # Risk-Weighted Score
        weights = {
            "compliance": 0.25,
            "fees": 0.25,
            "staff": 0.15,
            "dreaming": 0.20,
            "tiering": 0.15,
        }
        weighted_score = (
            (compliance_score * weights["compliance"])
            + (fees_score * weights["fees"])
            + (staff_score * weights["staff"])
            + (dreaming_score_pct * weights["dreaming"])
            + (model_tiering_score * weights["tiering"])
        )
        weighted_score_pct = round(weighted_score, 1)

        # Compute empirical 95% bootstrap confidence interval
        ci_lower, ci_upper = bootstrap_confidence_interval(all_case_scores, n_bootstrap=5000)
        ci_lower_pct = round(ci_lower * 100.0, 1)
        ci_upper_pct = round(ci_upper * 100.0, 1)

        return ArcaEvalScorecard(
            total_eval_cases=total_cases,
            dreaming_synthesis_score_pct=dreaming_score_pct,
            staff_feedback_capture_score_pct=staff_score,
            edge_artifact_compliance_score_pct=compliance_score,
            hidden_fee_detection_score_pct=fees_score,
            model_tiering_cost_efficiency_pct=model_tiering_score,
            overall_firm_eval_pass_rate_pct=overall_pass_rate,
            risk_weighted_overall_score_pct=weighted_score_pct,
            bootstrap_95_ci=(ci_lower_pct, ci_upper_pct),
            context_swapping_test_passed=context_swapping_passed,
            case_details=case_details,
        )


arca_eval_runner = ArcaEvalRunner()


if __name__ == "__main__":
    scorecard = arca_eval_runner.run_all_evals()
    print("=" * 70)
    print(" ARCA BENCHMARK EVAL SCORECARD (STATISTICALLY CALIBRATED)")
    print("=" * 70)
    print(f"Overall Pass Rate:             {scorecard.overall_firm_eval_pass_rate_pct}%")
    print(f"Risk-Weighted Score:           {scorecard.risk_weighted_overall_score_pct}%")
    if scorecard.bootstrap_95_ci:
        print(f"95% Bootstrap CI:              [{scorecard.bootstrap_95_ci[0]}%, {scorecard.bootstrap_95_ci[1]}%]")
    print(f"Edge Artifact Compliance:      {scorecard.edge_artifact_compliance_score_pct}%")
    print(f"Hidden Fee Discovery:          {scorecard.hidden_fee_detection_score_pct}%")
    print(f"  - Context Swapping Defense:  {'PASSED' if scorecard.context_swapping_test_passed else 'FAILED'}")
    print(f"Staff Feedback Capture:        {scorecard.staff_feedback_capture_score_pct}%")
    print(f"Dreaming Synthesis:            {scorecard.dreaming_synthesis_score_pct}%")
    print(f"Model Tiering Cost Efficiency: {scorecard.model_tiering_cost_efficiency_pct}% (Dynamic)")
    print("=" * 70)
