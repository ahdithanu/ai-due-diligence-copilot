"""Containment verifier — checks presence/absence of strings in output."""

from typing import Any, Dict, List, Optional

from eval.verifiers.base import BaseVerifier, EvalResult, VerifierType


class ContainmentVerifier(BaseVerifier):
    """Verifies output contains required strings and excludes forbidden ones.

    Use cases:
    - DLP: output must contain [REDACTED_SSN], must not contain raw SSN
    - Injection: response must contain 'blocked', must not contain payload
    - RBAC: masked content must not contain 'executive compensation'
    """

    verifier_type = VerifierType.CONTAINMENT

    def __init__(
        self,
        must_contain: Optional[List[str]] = None,
        must_not_contain: Optional[List[str]] = None,
        case_sensitive: bool = False,
    ):
        self.must_contain = must_contain or []
        self.must_not_contain = must_not_contain or []
        self.case_sensitive = case_sensitive

    def verify(
        self,
        expected: Any,
        actual: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvalResult:
        # Support actual being a string directly or a dict with a text field
        text = self._extract_text(actual)

        check_text = text if self.case_sensitive else text.lower()
        total_checks = len(self.must_contain) + len(self.must_not_contain)
        if total_checks == 0:
            return self._make_result(context, True, 1.0, "No containment checks defined")

        passed_checks = 0
        failures = []

        # Check must_contain
        for term in self.must_contain:
            check_term = term if self.case_sensitive else term.lower()
            if check_term in check_text:
                passed_checks += 1
            else:
                failures.append("missing: '{}'".format(term))

        # Check must_not_contain
        for term in self.must_not_contain:
            check_term = term if self.case_sensitive else term.lower()
            if check_term not in check_text:
                passed_checks += 1
            else:
                failures.append("found forbidden: '{}'".format(term))

        score = passed_checks / total_checks
        passed = len(failures) == 0
        reason = (
            "All {} containment checks passed".format(total_checks)
            if passed
            else "{}/{} checks failed: {}".format(
                len(failures), total_checks, "; ".join(failures[:3])
            )
        )

        return self._make_result(
            context, passed, score, reason,
            checks_passed=passed_checks,
            checks_total=total_checks,
            failures=failures,
        )

    def _extract_text(self, actual: Any) -> str:
        """Extract text string from various output formats."""
        if isinstance(actual, str):
            return actual
        if isinstance(actual, dict):
            # Try common field names
            for key in ("sanitized_text", "text", "content", "response", "message"):
                if key in actual:
                    return str(actual[key])
            return str(actual)
        return str(actual)
