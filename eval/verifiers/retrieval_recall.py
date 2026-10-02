"""Retrieval recall verifier for RAG evaluation."""

from typing import Any, Dict, List, Optional

from eval.verifiers.base import BaseVerifier, EvalResult, VerifierType


class RetrievalRecallVerifier(BaseVerifier):
    """Evaluates RAG retrieval quality using Recall@K and MRR.

    Recall@K = |expected ∩ actual_top_k| / |expected|
    MRR = 1 / rank_of_first_relevant_result
    """

    verifier_type = VerifierType.RETRIEVAL_RECALL

    def __init__(self, k: int = 5, pass_threshold: float = 0.6):
        self.k = k
        self.pass_threshold = pass_threshold

    def verify(
        self,
        expected: Any,
        actual: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvalResult:
        expected_ids = self._extract_expected_ids(expected)
        actual_ids = self._extract_actual_ids(actual)

        if not expected_ids:
            return self._make_result(
                context, True, 1.0, "No expected chunks — vacuously correct"
            )

        # Take top-K from actual
        top_k_ids = actual_ids[: self.k]

        # Recall@K
        hits = set(expected_ids) & set(top_k_ids)
        recall = len(hits) / len(expected_ids)

        # MRR — reciprocal rank of first relevant result
        mrr = 0.0
        for rank, chunk_id in enumerate(top_k_ids, start=1):
            if chunk_id in set(expected_ids):
                mrr = 1.0 / rank
                break

        passed = recall >= self.pass_threshold
        reason = "Recall@{k}={recall:.2f} (threshold {t:.2f}), MRR={mrr:.2f} — {h}/{e} relevant in top-{k}".format(
            k=self.k,
            recall=recall,
            t=self.pass_threshold,
            mrr=mrr,
            h=len(hits),
            e=len(expected_ids),
        )

        return self._make_result(
            context,
            passed,
            recall,
            reason,
            recall_at_k=recall,
            mrr=mrr,
            hits=list(hits),
            expected_ids=expected_ids,
            actual_top_k=top_k_ids,
        )

    def _extract_expected_ids(self, expected: Any) -> List[str]:
        if isinstance(expected, list):
            return [str(x) for x in expected]
        if isinstance(expected, dict):
            return [str(x) for x in expected.get("relevant_chunk_ids", [])]
        return []

    def _extract_actual_ids(self, actual: Any) -> List[str]:
        if isinstance(actual, list):
            # List of dicts with chunk_id, or list of strings
            ids = []
            for item in actual:
                if isinstance(item, dict):
                    ids.append(str(item.get("chunk_id", item.get("id", ""))))
                else:
                    ids.append(str(item))
            return ids
        if isinstance(actual, dict):
            results = actual.get("results", [])
            return [str(r.get("chunk_id", "")) for r in results if isinstance(r, dict)]
        return []
