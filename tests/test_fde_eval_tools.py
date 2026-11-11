import pytest
from typing import List

from eval.rogan_gladen import (
    calculate_tpr_tnr,
    calculate_cohens_kappa,
    rogan_gladen_correction,
    bootstrap_confidence_interval,
    calibrate_and_evaluate_production,
)
from eval.tool_trace_validator import ToolTraceValidator
from eval.rag_diagnostics import RAGDiagnosticSuite
from backend.services.fee_and_conflict_scanner import fee_and_conflict_scanner


# ============================================================================
# 1. Tests for Rogan-Gladen Bias Correction & Bootstrap CI
# ============================================================================

def test_tpr_tnr_calculation():
    # 80 True Positives, 20 False Negatives (100 actual positives) -> TPR = 0.80
    # 70 True Negatives, 30 False Positives (100 actual negatives) -> TNR = 0.70
    human = [1] * 100 + [0] * 100
    judge = [1] * 80 + [0] * 20 + [1] * 30 + [0] * 70

    metrics = calculate_tpr_tnr(human, judge)
    assert metrics["tpr"] == 0.80
    assert metrics["tnr"] == 0.70
    assert metrics["fpr"] == 0.30
    assert metrics["fnr"] == 0.20
    assert metrics["raw_accuracy"] == 0.75


def test_cohens_kappa():
    # Perfect agreement -> kappa = 1.0
    r1 = [1, 0, 1, 1, 0, 0, 1, 0]
    r2 = [1, 0, 1, 1, 0, 0, 1, 0]
    assert calculate_cohens_kappa(r1, r2) == 1.0

    # Skewed rater test (guards against chance agreement)
    human = [1] * 90 + [0] * 10
    all_ones_judge = [1] * 100
    kappa = calculate_cohens_kappa(human, all_ones_judge)
    # A judge that always guesses 1 achieves 90% raw agreement but kappa = 0.0
    assert kappa == 0.0


def test_rogan_gladen_correction():
    # p_obs = 0.80, TPR = 0.90, TNR = 0.85
    # denominator = 0.90 + 0.85 - 1.0 = 0.75
    # numerator = 0.80 + 0.85 - 1.0 = 0.65
    # theta_hat = 0.65 / 0.75 = 0.8667
    corrected = rogan_gladen_correction(observed_pass_rate=0.80, tpr=0.90, tnr=0.85)
    assert abs(corrected - (0.65 / 0.75)) < 1e-4

    # Test error when evaluator operates near chance (TPR + TNR - 1 < 0.05)
    with pytest.raises(ValueError) as exc:
        rogan_gladen_correction(observed_pass_rate=0.60, tpr=0.52, tnr=0.50)
    assert "operating near chance" in str(exc.value)


def test_bootstrap_confidence_interval():
    data = [1.0] * 80 + [0.0] * 20  # Mean = 0.80
    ci_low, ci_high = bootstrap_confidence_interval(data, n_bootstrap=1000, seed=42)
    assert 0.70 <= ci_low <= 0.80
    assert 0.80 <= ci_high <= 0.90


def test_calibrate_and_evaluate_production():
    human = [1] * 50 + [0] * 50
    judge = [1] * 45 + [0] * 5 + [1] * 10 + [0] * 40
    prod = [1] * 800 + [0] * 200

    report = calibrate_and_evaluate_production(human, judge, prod, n_bootstrap=500)
    assert report["calibration"]["tpr_sensitivity"] == 0.90
    assert report["calibration"]["tnr_specificity"] == 0.80
    assert report["calibration"]["is_calibrated"] is True
    assert report["production_inference"]["observed_pass_rate"] == 0.80
    assert report["production_inference"]["correction_applied"] is True


# ============================================================================
# 2. Tests for 4-Stage Tool Call Trace Validator
# ============================================================================

def test_tool_trace_validator_all_stages():
    validator = ToolTraceValidator()

    # Stage 1: Invalid tool selection
    bad_tool_trace = {
        "trace_id": "t-1",
        "expected_tool": "calculate_waterfall",
        "tool_call": {"name": "unregistered_magic_tool", "arguments": {}},
    }
    res1 = validator.validate_trace(bad_tool_trace)
    assert res1["overall_passed"] is False
    assert res1["first_failure_stage"] == "ToolSelection"

    # Stage 2: Schema / Argument generation failure (negative exit valuation)
    bad_args_trace = {
        "trace_id": "t-2",
        "expected_tool": "calculate_waterfall",
        "tool_call": {
            "name": "calculate_waterfall",
            "arguments": {"exit_valuation_usd": -100.0, "share_classes": ["Common"]},
        },
    }
    res2 = validator.validate_trace(bad_args_trace)
    assert res2["overall_passed"] is False
    assert res2["first_failure_stage"] == "GenArgs"

    # Stage 3: Tool execution failure (500 or timeout)
    exec_fail_trace = {
        "trace_id": "t-3",
        "expected_tool": "calculate_waterfall",
        "tool_call": {
            "name": "calculate_waterfall",
            "arguments": {"exit_valuation_usd": 100_000_000.0, "share_classes": ["Common"]},
        },
        "tool_execution": {"status": "TIMEOUT", "error_message": "Gateway timeout after 5000ms"},
    }
    res3 = validator.validate_trace(exec_fail_trace)
    assert res3["overall_passed"] is False
    assert res3["first_failure_stage"] == "ExecTool"

    # Stage 4: Output handling failure (model ignored payload tokens)
    output_fail_trace = {
        "trace_id": "t-4",
        "expected_tool": "calculate_waterfall",
        "tool_call": {
            "name": "calculate_waterfall",
            "arguments": {"exit_valuation_usd": 100_000_000.0, "share_classes": ["Common"]},
        },
        "tool_execution": {"status": "SUCCESS", "output": {"Common": 100_000_000.0}},
        "final_response": "The overall venture environment is robust.",
        "expected_output_tokens": ["$100M"],
    }
    res4 = validator.validate_trace(output_fail_trace)
    assert res4["overall_passed"] is False
    assert res4["first_failure_stage"] == "HandleOut"

    # Successful trace through all 4 stages
    clean_trace = {
        "trace_id": "t-clean",
        "expected_tool": "calculate_waterfall",
        "tool_call": {
            "name": "calculate_waterfall",
            "arguments": {"exit_valuation_usd": 100_000_000.0, "share_classes": ["Common"]},
        },
        "tool_execution": {"status": "SUCCESS", "output": {"Common": 100_000_000.0}},
        "final_response": "The calculated waterfall allocates $100M to Common stock.",
        "expected_output_tokens": ["$100M"],
    }
    res_clean = validator.validate_trace(clean_trace)
    assert res_clean["overall_passed"] is True
    assert res_clean["first_failure_stage"] is None

    # Transition matrix calculation
    matrix_res = validator.compute_transition_failure_matrix([res1, res2, res3, res4, res_clean])
    assert matrix_res["total_traces"] == 5
    assert matrix_res["total_passed"] == 1
    assert matrix_res["total_failed"] == 4
    assert matrix_res["pass_rate_pct"] == 20.0
    text_hm = validator.format_heatmap_text(matrix_res)
    assert "Transition Failure Heatmap" in text_hm


# ============================================================================
# 3. Tests for RAG Diagnostic Suite & Context-Swapping
# ============================================================================

def test_rag_diagnostic_retrieval_and_swapping():
    suite = RAGDiagnosticSuite()
    assert len(suite.dataset) >= 30

    # Retrieval Ranking Metrics
    sim_rankings = [
        {"query_id": "q1", "expected_chunk_id": "c1", "retrieved_chunk_ids": ["c1", "c2", "c3"]},
        {"query_id": "q2", "expected_chunk_id": "c2", "retrieved_chunk_ids": ["c1", "c2", "c3"]},
        {"query_id": "q3", "expected_chunk_id": "c99", "retrieved_chunk_ids": ["c1", "c2", "c3"]},
    ]
    ret_res = suite.evaluate_retrieval_ranking(sim_rankings, k_values=[1, 3])
    # q1: rank 1 (RR = 1.0)
    # q2: rank 2 (RR = 0.5)
    # q3: not found (RR = 0.0)
    # MRR = (1.0 + 0.5 + 0.0) / 3 = 0.50
    assert ret_res["mrr"] == 0.5
    assert ret_res["hit_rates"]["hit_rate@1"] == 33.3
    assert ret_res["hit_rates"]["hit_rate@3"] == 66.7

    # Context Swapping Test with faithful generator
    diag_res = suite.evaluate_context_swapping()
    assert diag_res["faithful_grounded_rate_pct"] == 100.0
    assert diag_res["context_swapping_defense_rate_pct"] == 100.0
    assert diag_res["parametric_leakage_rate_pct"] == 0.0
    assert diag_res["is_production_ready"] is True

    # Context Swapping with Hallucinating Generator (leaks target fact when context is swapped)
    def leaking_generator(query: str, context: str) -> str:
        # Ignores context, emits static ARR fact
        return "The ARR is $9.35M regardless of context."

    leaking_res = suite.evaluate_context_swapping(leaking_generator)
    assert leaking_res["parametric_leakage_rate_pct"] > 0.0
    assert leaking_res["is_production_ready"] is False


# ============================================================================
# 4. Tests for Fee Scanner Context-Swapping & Clean Baseline
# ============================================================================

def test_fee_scanner_clean_baseline_context_swap():
    # Clean baseline agreement should produce ZERO false positive findings
    clean_text = (
        "NVCA Standard Series A Preferred Stock Purchase Agreement. "
        "Holders of Series A Preferred Stock receive standard 1.0x non-participating liquidation preference. "
        "No management fees, monitoring fees, or transaction success fees are authorized."
    )
    clean_findings = fee_and_conflict_scanner.scan_document_text(clean_text)
    assert len(clean_findings) == 0

    # Hostile agreement text should extract exact traps
    hostile_text = (
        "Target shall pay $240,000 annually to Apex Horizons LLC, an entity wholly owned by CEO. "
        "Advisor disclaims all fiduciary duties to Company. "
        "Seed SAFE converts into 2.0x liquidation preference senior to Common Stock."
    )
    hostile_findings = fee_and_conflict_scanner.scan_document_text(hostile_text)
    assert len(hostile_findings) == 3
    cats = {f.category for f in hostile_findings}
    assert "RELATED_PARTY" in cats
    assert "NON_FIDUCIARY" in cats
    assert "LIQUIDATION_RATCHET" in cats
