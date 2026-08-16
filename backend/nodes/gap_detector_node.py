import uuid
import logging
from typing import Optional, List, Set, Dict, Any

from backend.domain.schemas import (
    DiligenceState,
    DiligenceStatus,
    DiligenceQuestion,
    MaterialityLevel,
    ClaimType,
    ContradictionRecord,
    ClaimNode
)
from backend.engine.node import BaseNode
from backend.engine.model_adapter import ModelAdapter

logger = logging.getLogger(__name__)


class GapDetectorNode(BaseNode):
    """
    Gap Detector Node: Evaluates missing evidence, unverified claims, contradictions, and high-materiality risks
    to produce ranked DiligenceQuestions. Appends to state.open_questions.
    """

    def __init__(
        self,
        name: str = "GapDetector",
        model_adapter: Optional[ModelAdapter] = None
    ):
        super().__init__(name=name, description="Evaluates diligence gaps, unverified claims, and risks to generate ranked questions", model_adapter=model_adapter)

    async def process(self, state: DiligenceState) -> DiligenceState:
        existing_question_texts = {q.question.lower() for q in state.open_questions}
        new_questions: List[DiligenceQuestion] = []

        if self.model_adapter:
            prompt = (
                f"Identify diligence gaps, missing evidence, unverified assumptions, and risk mitigations for company '{state.company_name}'.\n"
                f"Contradictions Count: {len(state.contradictions)}\n"
                f"Risk Register Count: {len(state.risk_register)}\n"
                f"Specialist Domains Evaluated: {list(state.specialist_analyses.keys())}\n"
                f"Produce ranked DiligenceQuestion records with priority 1 (highest) to N."
            )
            generated = await self.model_adapter.generate(
                prompt=prompt,
                response_model=List[DiligenceQuestion]
            )
            if isinstance(generated, list):
                new_questions.extend(generated)
        else:
            # Deterministic / Heuristic Gap Detection
            # 1. Convert Contradictions into Priority 1 Diligence Questions
            for contra in state.contradictions:
                q_text = f"Can management clarify the following data discrepancy: {contra.description}?"
                if q_text.lower() not in existing_question_texts:
                    q = DiligenceQuestion(
                        id=str(uuid.uuid4()),
                        question=q_text,
                        reason_it_matters="Resolving data discrepancies between deck and financial records is critical for valuation and trust.",
                        related_risk_or_thesis=f"Data integrity & financial reporting risk (Contradiction {contra.id})",
                        required_evidence="Audited financial statements, bank statements, or reconciled revenue schedules.",
                        materiality=contra.materiality,
                        priority=1,
                        status="OPEN"
                    )
                    new_questions.append(q)

            # 2. Evaluate High-Materiality Risks in state.risk_register
            for risk in state.risk_register:
                if risk.materiality in [MaterialityLevel.HIGH, MaterialityLevel.CRITICAL]:
                    q_text = f"What mitigation strategy and evidence exists for risk: '{risk.text}'?"
                    if q_text.lower() not in existing_question_texts:
                        prio = 1 if risk.materiality == MaterialityLevel.CRITICAL else 2
                        q = DiligenceQuestion(
                            id=str(uuid.uuid4()),
                            question=q_text,
                            reason_it_matters=f"High materiality risk directly impacts investment outcome and risk-adjusted return.",
                            related_risk_or_thesis=risk.text,
                            required_evidence="Management response, insurance policies, key-man agreements, or technical mitigation plan.",
                            materiality=risk.materiality,
                            priority=prio,
                            status="OPEN"
                        )
                        new_questions.append(q)

            # 3. Identify Unverified Assumptions or Claims lacking citations
            for domain, analysis in state.specialist_analyses.items():
                for claim in analysis.claims:
                    if claim.claim_type in [ClaimType.ASSUMPTION, ClaimType.UNRESOLVED_QUESTION] or not claim.evidence_ids:
                        q_text = f"What empirical evidence supports the {domain} claim: '{claim.text}'?"
                        if q_text.lower() not in existing_question_texts:
                            q = DiligenceQuestion(
                                id=str(uuid.uuid4()),
                                question=q_text,
                                reason_it_matters=f"Unverified assumption in {domain} domain introduces unquantified downside risk.",
                                related_risk_or_thesis=f"Unverified {domain} assumption",
                                required_evidence=f"Primary documentation, contract, or operational metric for {domain}.",
                                materiality=claim.materiality,
                                priority=2 if claim.materiality == MaterialityLevel.HIGH else 3,
                                status="OPEN"
                            )
                            new_questions.append(q)

            # 4. Check for missing core diligence domains
            required_domains = ["Financial", "Market", "Competitive", "Customer", "Product", "Risk", "UnitEconomics"]
            missing_domains = [d for d in required_domains if d not in state.specialist_analyses]

            for m_domain in missing_domains:
                q_text = f"What primary documentation and data is available to conduct full {m_domain} diligence?"
                if q_text.lower() not in existing_question_texts:
                    q = DiligenceQuestion(
                        id=str(uuid.uuid4()),
                        question=q_text,
                        reason_it_matters=f"Missing specialist analysis for {m_domain} leaves core diligence pillars incomplete.",
                        related_risk_or_thesis=f"Incomplete {m_domain} diligence pillar",
                        required_evidence=f"Detailed materials and data room access for {m_domain}.",
                        materiality=MaterialityLevel.HIGH,
                        priority=2,
                        status="OPEN"
                    )
                    new_questions.append(q)

        # Append new questions avoiding duplicates
        for q in new_questions:
            if q.question.lower() not in existing_question_texts:
                state.open_questions.append(q)
                existing_question_texts.add(q.question.lower())

        # Sort state.open_questions by priority ascending (1, 2, 3...)
        state.open_questions.sort(key=lambda x: (x.priority, 0 if x.materiality == MaterialityLevel.CRITICAL else (1 if x.materiality == MaterialityLevel.HIGH else 2)))

        return state
