"""Tests for the eval framework: verifiers, task loading, dataset loading, and runner."""
import json
import pytest
from pathlib import Path

from eval.verifiers import get_verifier, ExactMatchVerifier, ContainmentVerifier
from eval.verifiers import RetrievalRecallVerifier, LLMJudgeVerifier
from eval.verifiers.base import EvalResult, VerifierType
from eval.run_eval import EvalRunner, TaskConfig, ServiceExecutor, run_verifier


# ──────────────────────────────────────────────
# 1. Verifier factory
# ──────────────────────────────────────────────

class TestVerifierFactory:
    def test_get_exact_match(self):
        v = get_verifier("exact_match")
        assert isinstance(v, ExactMatchVerifier)

    def test_get_containment(self):
        v = get_verifier("containment", must_contain=["hello"])
        assert isinstance(v, ContainmentVerifier)

    def test_get_retrieval_recall(self):
        v = get_verifier("retrieval_recall", k=10)
        assert isinstance(v, RetrievalRecallVerifier)

    def test_get_llm_judge(self):
        v = get_verifier("llm_judge", scale=5)
        assert isinstance(v, LLMJudgeVerifier)

    def test_unknown_verifier_raises(self):
        with pytest.raises(ValueError, match="Unknown verifier"):
            get_verifier("nonexistent_verifier")


# ──────────────────────────────────────────────
# 2. ExactMatch verifier
# ──────────────────────────────────────────────

class TestExactMatchVerifier:
    def test_numeric_match(self):
        v = ExactMatchVerifier(atol=0.01)
        ctx = {"task_id": "test", "sample_id": "s1"}
        r = v.verify(100.0, 100.005, ctx)
        assert r.passed is True
        assert r.score == 1.0

    def test_numeric_mismatch(self):
        v = ExactMatchVerifier(atol=0.001)
        r = v.verify(100.0, 101.0, {"task_id": "t", "sample_id": "s"})
        assert r.passed is False
        assert r.score == 0.0

    def test_string_match_normalized(self):
        v = ExactMatchVerifier(normalize_strings=True)
        r = v.verify("FINANCIAL_ANALYSIS", "  financial_analysis  ", {"task_id": "t", "sample_id": "s"})
        assert r.passed is True

    def test_string_mismatch(self):
        v = ExactMatchVerifier()
        r = v.verify("EXPECTED", "ACTUAL", {"task_id": "t", "sample_id": "s"})
        assert r.passed is False

    def test_dict_match(self):
        v = ExactMatchVerifier()
        r = v.verify({"a": 1, "b": "hello"}, {"a": 1, "b": "hello"}, {"task_id": "t", "sample_id": "s"})
        assert r.passed is True

    def test_dict_mismatch(self):
        v = ExactMatchVerifier()
        r = v.verify({"a": 1}, {"a": 2}, {"task_id": "t", "sample_id": "s"})
        assert r.passed is False


# ──────────────────────────────────────────────
# 3. Containment verifier
# ──────────────────────────────────────────────

class TestContainmentVerifier:
    def test_must_contain_pass(self):
        v = ContainmentVerifier(must_contain=["redacted", "ssn"])
        r = v.verify({}, "[REDACTED_SSN] was found and redacted", {"task_id": "t", "sample_id": "s"})
        assert r.passed is True
        assert r.score == 1.0

    def test_must_contain_fail(self):
        v = ContainmentVerifier(must_contain=["[REDACTED_SSN]"])
        r = v.verify({}, "No redaction happened 123-45-6789", {"task_id": "t", "sample_id": "s"})
        assert r.passed is False

    def test_must_not_contain_pass(self):
        v = ContainmentVerifier(must_not_contain=["123-45-6789"])
        r = v.verify({}, "SSN was [REDACTED_SSN]", {"task_id": "t", "sample_id": "s"})
        assert r.passed is True

    def test_must_not_contain_fail(self):
        v = ContainmentVerifier(must_not_contain=["password123"])
        r = v.verify({}, "The password is password123", {"task_id": "t", "sample_id": "s"})
        assert r.passed is False

    def test_combined_checks(self):
        v = ContainmentVerifier(
            must_contain=["[REDACTED_SSN]"],
            must_not_contain=["123-45-6789"],
        )
        r = v.verify({}, "[REDACTED_SSN] was sanitized", {"task_id": "t", "sample_id": "s"})
        assert r.passed is True
        assert r.score == 1.0

    def test_dict_actual_extracts_text(self):
        v = ContainmentVerifier(must_contain=["redacted"])
        r = v.verify({}, {"sanitized_text": "Data was [REDACTED]"}, {"task_id": "t", "sample_id": "s"})
        assert r.passed is True


# ──────────────────────────────────────────────
# 4. RetrievalRecall verifier
# ──────────────────────────────────────────────

class TestRetrievalRecallVerifier:
    def test_perfect_recall(self):
        v = RetrievalRecallVerifier(k=5, pass_threshold=0.6)
        expected = {"relevant_chunk_ids": ["c1", "c2"]}
        actual = {"results": [
            {"chunk_id": "c1"}, {"chunk_id": "c2"}, {"chunk_id": "c3"},
        ]}
        r = v.verify(expected, actual, {"task_id": "t", "sample_id": "s"})
        assert r.passed is True
        assert r.score == 1.0

    def test_partial_recall(self):
        v = RetrievalRecallVerifier(k=3, pass_threshold=0.5)
        expected = {"relevant_chunk_ids": ["c1", "c2"]}
        actual = {"results": [{"chunk_id": "c1"}, {"chunk_id": "c99"}]}
        r = v.verify(expected, actual, {"task_id": "t", "sample_id": "s"})
        assert r.score == 0.5
        assert r.passed is True  # 0.5 >= 0.5 threshold

    def test_zero_recall(self):
        v = RetrievalRecallVerifier(k=5, pass_threshold=0.6)
        expected = {"relevant_chunk_ids": ["c1"]}
        actual = {"results": [{"chunk_id": "c99"}]}
        r = v.verify(expected, actual, {"task_id": "t", "sample_id": "s"})
        assert r.score == 0.0
        assert r.passed is False

    def test_mrr_calculation(self):
        v = RetrievalRecallVerifier(k=5)
        expected = {"relevant_chunk_ids": ["c3"]}
        actual = {"results": [
            {"chunk_id": "c1"}, {"chunk_id": "c2"}, {"chunk_id": "c3"},
        ]}
        r = v.verify(expected, actual, {"task_id": "t", "sample_id": "s"})
        # c3 is at rank 3, so MRR = 1/3
        assert r.metadata["mrr"] == pytest.approx(1 / 3, abs=0.01)


# ──────────────────────────────────────────────
# 5. LLMJudge verifier
# ──────────────────────────────────────────────

class TestLLMJudgeVerifier:
    def test_grounded_answer_scores_well(self):
        v = LLMJudgeVerifier(pass_threshold=0.5)
        answer = (
            "Based on the financial statements, the company reported $12M ARR. "
            "According to the audit report, gross margins are 78%. "
            "The data indicates strong growth trajectory.\n\n"
            "Key findings:\n"
            "- Revenue growing 45% YoY\n"
            "- Net retention at 125%\n"
            "- Strong unit economics per the analysis"
        )
        r = v.verify({}, answer, {"task_id": "t", "sample_id": "s"})
        assert r.passed is True
        assert r.score >= 0.5

    def test_empty_answer_scores_poorly(self):
        v = LLMJudgeVerifier(pass_threshold=0.6)
        r = v.verify({}, "I don't know.", {"task_id": "t", "sample_id": "s"})
        assert r.score < 0.6

    def test_judge_prompt_format(self):
        v = LLMJudgeVerifier()
        prompt = v._format_judge_prompt("What is ARR?", "The ARR is $12M.")
        assert "RUBRIC" in prompt
        assert "USER QUERY" in prompt
        assert "What is ARR?" in prompt


# ──────────────────────────────────────────────
# 6. Task YAML loading
# ──────────────────────────────────────────────

class TestTaskLoading:
    def test_load_all_tasks(self):
        runner = EvalRunner()
        tasks = runner.load_tasks()
        assert len(tasks) >= 6
        task_ids = [t.task_id for t in tasks]
        assert "injection_defense" in task_ids
        assert "intent_routing" in task_ids
        assert "dlp_redaction" in task_ids

    def test_load_filtered_tasks(self):
        runner = EvalRunner()
        tasks = runner.load_tasks(task_filter=["injection_defense"])
        assert len(tasks) == 1
        assert tasks[0].task_id == "injection_defense"

    def test_task_config_fields(self):
        runner = EvalRunner()
        tasks = runner.load_tasks(task_filter=["injection_defense"])
        t = tasks[0]
        assert t.name == "Injection Attack Defense"
        assert t.dataset == "attack_corpus.jsonl"
        assert t.verifier == "containment"
        assert t.service == "intent_router"
        assert t.method == "validate_ingress_guardrails"


# ──────────────────────────────────────────────
# 7. Dataset JSONL loading
# ──────────────────────────────────────────────

class TestDatasetLoading:
    def test_load_attack_corpus(self):
        runner = EvalRunner()
        samples = runner.load_dataset("attack_corpus.jsonl")
        assert len(samples) >= 10
        assert all("sample_id" in s for s in samples)
        assert all("input" in s for s in samples)

    def test_load_intent_routing(self):
        runner = EvalRunner()
        samples = runner.load_dataset("intent_routing.jsonl")
        assert len(samples) >= 12

    def test_load_dlp_samples(self):
        runner = EvalRunner()
        samples = runner.load_dataset("dlp_samples.jsonl")
        assert len(samples) >= 6

    def test_all_datasets_valid_json(self):
        """Validate every JSONL file in the datasets directory."""
        datasets_dir = Path("eval/datasets")
        for jsonl_file in datasets_dir.glob("*.jsonl"):
            with open(jsonl_file) as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            json.loads(line)
                        except json.JSONDecodeError:
                            pytest.fail(
                                "Invalid JSON on line {} of {}".format(i, jsonl_file.name)
                            )


# ──────────────────────────────────────────────
# 8. EvalRunner initialization
# ──────────────────────────────────────────────

class TestEvalRunner:
    def test_runner_init(self):
        runner = EvalRunner()
        assert runner.tasks_dir.exists()
        assert runner.datasets_dir.exists()

    def test_run_injection_defense(self):
        """Run injection defense eval end-to-end.

        Current baseline: 58% — the eval correctly identifies that some
        injection patterns (DAN mode, SUDO override, indirect translation
        attacks) bypass the regex guardrails. This is a real finding.
        """
        runner = EvalRunner()
        result = runner.run(task_filter=["injection_defense"], verbose=False)
        assert result.total_tasks == 1
        assert result.total_samples >= 10
        tr = result.task_results["injection_defense"]
        assert tr.pass_rate >= 0.50  # baseline: 58% — improve guardrails to raise this
        print("  Injection defense: {}/{} passed ({:.0f}%)".format(
            tr.samples_passed, tr.samples_run, tr.pass_rate * 100
        ))

    def test_run_dlp_redaction(self):
        """Run DLP redaction eval end-to-end."""
        runner = EvalRunner()
        result = runner.run(task_filter=["dlp_redaction"], verbose=False)
        tr = result.task_results["dlp_redaction"]
        assert tr.pass_rate >= 0.70
        print("  DLP redaction: {}/{} passed ({:.0f}%)".format(
            tr.samples_passed, tr.samples_run, tr.pass_rate * 100
        ))

    def test_scorecard_no_crash(self):
        """Ensure scorecard printing doesn't crash."""
        runner = EvalRunner()
        result = runner.run(task_filter=["injection_defense"], verbose=False)
        runner.print_scorecard(result)  # should print without error


# ──────────────────────────────────────────────
# 9. Full suite smoke test
# ──────────────────────────────────────────────

class TestFullSuite:
    def test_run_all_tasks(self):
        """Smoke test: run the entire eval suite."""
        runner = EvalRunner()
        result = runner.run(verbose=False)
        assert result.total_tasks >= 5
        assert result.total_samples >= 30
        runner.print_scorecard(result)
        print("  Full suite: {:.0f}% overall pass rate".format(
            result.overall_pass_rate * 100
        ))
