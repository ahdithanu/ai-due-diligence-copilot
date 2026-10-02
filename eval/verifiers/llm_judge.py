"""LLM-as-judge verifier for subjective quality (memos, groundedness, chat).

In production this calls an LLM to grade output quality. For now it uses
rule-based heuristics that check the same things a real judge prompt would.
The _format_judge_prompt() method shows exactly what the LLM call looks like.
"""

import re
from typing import Any, Dict, Optional

from eval.verifiers.base import BaseVerifier, EvalResult, VerifierType


# Default grounding rubric used when none is provided
DEFAULT_GROUNDING_RUBRIC = """
Score the response on a 1-5 scale:
5 — Fully grounded: every claim cites specific evidence; no hallucination
4 — Mostly grounded: 1-2 minor unsupported claims; core answer is correct
3 — Partially grounded: some correct claims, some unsupported; mixed quality
2 — Mostly ungrounded: significant hallucination or fabrication present
1 — Ungrounded: no evidence cited, speculative, or clearly wrong
""".strip()


class LLMJudgeVerifier(BaseVerifier):
    """Evaluates subjective output quality using LLM-as-judge paradigm.

    Currently uses rule-based scoring. Set use_live_model=True (and provide
    an API key) to use an actual LLM for evaluation.

    Scoring dimensions (rule-based):
    - Evidence citation: references sources / data / documents
    - Answer depth: sufficient length, not a one-liner
    - Hedging when uncertain: uses cautious language when evidence is thin
    - Structural quality: organized, uses sections or bullet points
    """

    verifier_type = VerifierType.LLM_JUDGE

    def __init__(
        self,
        rubric: str = DEFAULT_GROUNDING_RUBRIC,
        scale: int = 5,
        pass_threshold: float = 0.6,
        use_live_model: bool = False,
    ):
        self.rubric = rubric
        self.scale = scale
        self.pass_threshold = pass_threshold
        self.use_live_model = use_live_model

    def verify(
        self,
        expected: Any,
        actual: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvalResult:
        text = str(actual.get("content", actual) if isinstance(actual, dict) else actual)
        query = ""
        if context:
            query = context.get("query", "")

        if self.use_live_model:
            # Placeholder for real LLM judge call
            return self._make_result(
                context, False, 0.0,
                "Live model judging not configured — set API key",
            )

        # Rule-based scoring
        scores = {}
        scores["evidence_citation"] = self._score_evidence(text)
        scores["answer_depth"] = self._score_depth(text)
        scores["hedging_appropriateness"] = self._score_hedging(text, context)
        scores["structural_quality"] = self._score_structure(text)

        avg_score = sum(scores.values()) / len(scores)
        normalized = avg_score / self.scale
        passed = normalized >= self.pass_threshold

        breakdown = ", ".join(
            "{}: {:.1f}/{}".format(k, v, self.scale) for k, v in scores.items()
        )

        return self._make_result(
            context,
            passed,
            normalized,
            "LLM Judge (rule-based): avg {:.2f}/{} [{}]".format(
                avg_score, self.scale, breakdown
            ),
            dimension_scores=scores,
            judge_prompt=self._format_judge_prompt(query, text),
        )

    def _score_evidence(self, text: str) -> float:
        """Score 1-5: does the answer reference evidence/sources?"""
        evidence_patterns = [
            r"\[source", r"\[ref", r"according to", r"based on",
            r"evidence shows", r"data indicates", r"per the",
            r"as stated in", r"the document", r"the report",
            r"financial statements", r"audit report",
        ]
        matches = sum(1 for p in evidence_patterns if re.search(p, text, re.I))
        if matches >= 4:
            return 5.0
        if matches >= 2:
            return 4.0
        if matches >= 1:
            return 3.0
        if len(text) > 200:
            return 2.0
        return 1.0

    def _score_depth(self, text: str) -> float:
        """Score 1-5: is the answer substantive enough?"""
        word_count = len(text.split())
        if word_count >= 150:
            return 5.0
        if word_count >= 80:
            return 4.0
        if word_count >= 40:
            return 3.0
        if word_count >= 15:
            return 2.0
        return 1.0

    def _score_hedging(self, text: str, context: Optional[Dict] = None) -> float:
        """Score 1-5: does the answer hedge appropriately on uncertainty?"""
        hedging_words = [
            "uncertain", "may", "might", "appears to", "seems",
            "insufficient evidence", "cannot confirm", "unclear",
            "limited data", "further review",
        ]
        hedge_count = sum(1 for w in hedging_words if w in text.lower())
        should_hedge = False
        if context and context.get("should_hedge"):
            should_hedge = True

        if should_hedge:
            # Should hedge and does hedge
            return min(5.0, 3.0 + hedge_count)
        else:
            # Shouldn't need to hedge — light hedging is fine, excessive is bad
            if hedge_count == 0:
                return 5.0
            if hedge_count <= 2:
                return 4.0
            return 2.0

    def _score_structure(self, text: str) -> float:
        """Score 1-5: is the answer well-organized?"""
        has_bullets = bool(re.search(r"^[\s]*[-•*]\s", text, re.M))
        has_numbers = bool(re.search(r"^[\s]*\d+[.)]\s", text, re.M))
        has_sections = bool(re.search(r"^#+\s|^[A-Z][A-Za-z ]+:\s", text, re.M))
        has_paragraphs = text.count("\n\n") >= 1

        structure_score = sum([has_bullets, has_numbers, has_sections, has_paragraphs])
        return min(5.0, 2.0 + structure_score)

    def _format_judge_prompt(self, query: str, response: str) -> str:
        """Format the prompt that would be sent to an LLM judge.

        This is the exact prompt you'd use with GPT-4 or Gemini to grade
        subjective output quality. Exposed for interview discussion.
        """
        return """You are an expert evaluator for an AI due diligence copilot.

RUBRIC:
{rubric}

USER QUERY:
{query}

AGENT RESPONSE:
{response}

INSTRUCTIONS:
1. Read the rubric carefully.
2. Evaluate the agent response against each criterion.
3. Provide a score from 1 to {scale}.
4. Explain your reasoning in 2-3 sentences.

OUTPUT FORMAT (JSON):
{{"score": <int>, "reasoning": "<string>"}}""".format(
            rubric=self.rubric,
            query=query,
            response=response[:2000],
            scale=self.scale,
        )
