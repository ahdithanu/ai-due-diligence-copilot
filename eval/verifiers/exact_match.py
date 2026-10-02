"""Exact match verifier for deterministic outputs (math, DLP, RBAC)."""

import math
from typing import Any, Dict, Optional

from eval.verifiers.base import BaseVerifier, EvalResult, VerifierType


class ExactMatchVerifier(BaseVerifier):
    """Verifies that actual output exactly matches expected output.

    Supports numeric tolerance for float comparison and optional
    string normalization (strip whitespace, case-insensitive).
    """

    verifier_type = VerifierType.EXACT_MATCH

    def __init__(self, atol: float = 1e-6, normalize_strings: bool = True):
        self.atol = atol
        self.normalize_strings = normalize_strings

    def verify(
        self,
        expected: Any,
        actual: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvalResult:
        # Numeric comparison with tolerance
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            match = math.isclose(expected, actual, abs_tol=self.atol)
            reason = (
                "Numeric match within tolerance"
                if match
                else "Expected {}, got {} (tol={})".format(expected, actual, self.atol)
            )
            return self._make_result(context, match, 1.0 if match else 0.0, reason)

        # String comparison
        if isinstance(expected, str) and isinstance(actual, str):
            exp = expected.strip().lower() if self.normalize_strings else expected
            act = actual.strip().lower() if self.normalize_strings else actual
            match = exp == act
            reason = "String match" if match else "Expected '{}', got '{}'".format(
                expected[:80], actual[:80]
            )
            return self._make_result(context, match, 1.0 if match else 0.0, reason)

        # Dict comparison (recursive key-value check)
        if isinstance(expected, dict) and isinstance(actual, dict):
            return self._compare_dicts(expected, actual, context)

        # List comparison
        if isinstance(expected, list) and isinstance(actual, list):
            if len(expected) != len(actual):
                return self._make_result(
                    context, False, 0.0,
                    "List length mismatch: expected {}, got {}".format(
                        len(expected), len(actual)
                    ),
                )
            matches = sum(
                1
                for e, a in zip(expected, actual)
                if self._values_match(e, a)
            )
            score = matches / len(expected) if expected else 1.0
            return self._make_result(
                context, score == 1.0, score,
                "{}/{} elements match".format(matches, len(expected)),
            )

        # Fallback: direct equality
        match = expected == actual
        return self._make_result(
            context, match, 1.0 if match else 0.0,
            "Direct match" if match else "Type/value mismatch",
        )

    def _values_match(self, expected: Any, actual: Any) -> bool:
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            return math.isclose(expected, actual, abs_tol=self.atol)
        if isinstance(expected, str) and isinstance(actual, str):
            if self.normalize_strings:
                return expected.strip().lower() == actual.strip().lower()
            return expected == actual
        return expected == actual

    def _compare_dicts(
        self,
        expected: dict,
        actual: dict,
        context: Optional[Dict[str, Any]],
    ) -> EvalResult:
        all_keys = set(expected.keys()) | set(actual.keys())
        if not all_keys:
            return self._make_result(context, True, 1.0, "Both dicts empty")

        matches = 0
        mismatches = []
        for key in expected:
            if key not in actual:
                mismatches.append("missing key '{}'".format(key))
            elif self._values_match(expected[key], actual[key]):
                matches += 1
            else:
                mismatches.append(
                    "key '{}': expected {}, got {}".format(
                        key, expected[key], actual[key]
                    )
                )

        score = matches / len(expected) if expected else 1.0
        passed = score == 1.0 and not mismatches
        reason = "All keys match" if passed else "; ".join(mismatches[:3])
        return self._make_result(context, passed, score, reason)
