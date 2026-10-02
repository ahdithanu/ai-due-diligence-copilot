"""Base verifier classes and result types for the eval framework."""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict
from enum import Enum


class VerifierType(str, Enum):
    """Types of verification strategies."""
    EXACT_MATCH = "exact_match"
    CONTAINMENT = "containment"
    RETRIEVAL_RECALL = "retrieval_recall"
    LLM_JUDGE = "llm_judge"


@dataclass
class EvalResult:
    """Result of evaluating a single sample against expected output."""
    task_id: str
    sample_id: str
    passed: bool
    score: float  # 0.0 to 1.0
    reason: str
    verifier_type: str
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseVerifier:
    """Abstract base class for all verifiers."""

    verifier_type: VerifierType = VerifierType.EXACT_MATCH

    def verify(
        self,
        expected: Any,
        actual: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvalResult:
        """Verify actual output against expected. Must be overridden."""
        raise NotImplementedError

    def _ctx(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return context or {}

    def _make_result(
        self,
        context: Optional[Dict[str, Any]],
        passed: bool,
        score: float,
        reason: str,
        **extra_meta,
    ) -> EvalResult:
        ctx = self._ctx(context)
        return EvalResult(
            task_id=ctx.get("task_id", "unknown"),
            sample_id=ctx.get("sample_id", "unknown"),
            passed=passed,
            score=score,
            reason=reason,
            verifier_type=self.verifier_type.value,
            latency_ms=ctx.get("latency_ms", 0.0),
            metadata=extra_meta,
        )
