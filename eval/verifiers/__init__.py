"""Verifier factory and exports."""

from eval.verifiers.base import BaseVerifier, EvalResult, VerifierType
from eval.verifiers.exact_match import ExactMatchVerifier
from eval.verifiers.containment import ContainmentVerifier
from eval.verifiers.retrieval_recall import RetrievalRecallVerifier
from eval.verifiers.llm_judge import LLMJudgeVerifier

_REGISTRY = {
    "exact_match": ExactMatchVerifier,
    "containment": ContainmentVerifier,
    "retrieval_recall": RetrievalRecallVerifier,
    "llm_judge": LLMJudgeVerifier,
}


def get_verifier(verifier_type: str, **config) -> BaseVerifier:
    """Factory that maps a verifier type string to an instantiated verifier."""
    cls = _REGISTRY.get(verifier_type)
    if cls is None:
        raise ValueError(
            "Unknown verifier type '{}'. Available: {}".format(
                verifier_type, list(_REGISTRY.keys())
            )
        )
    return cls(**config)


__all__ = [
    "BaseVerifier",
    "EvalResult",
    "VerifierType",
    "ExactMatchVerifier",
    "ContainmentVerifier",
    "RetrievalRecallVerifier",
    "LLMJudgeVerifier",
    "get_verifier",
]
