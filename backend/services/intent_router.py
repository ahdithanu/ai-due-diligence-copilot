import re
from typing import Tuple, List, Optional
from backend.domain.schemas import (
    UserIntent,
    IntentClassificationResult,
    IngressGuardrailResult
)

# Standard institutional out-of-scope canned response
OUT_OF_SCOPE_RESPONSE = (
    "I am your Enterprise AI Due Diligence Copilot, specialized strictly in institutional investment analysis, "
    "financial models, cap tables, document rooms, and tenant lease underwriting. "
    "I cannot assist with general inquiries outside this investment deal room."
)

PROMPT_INJECTION_RESPONSE = (
    "Security Exception: Your query triggered enterprise system security guardrails (potential prompt injection "
    "or instruction override). This interaction has been recorded in the immutable compliance audit log."
)

class IntentRouterService:
    """
    Edge Ingress Guardrails & Intent Classifier Node.
    
    Protects downstream heavy RAG pipelines, LLM models, and database resources by:
    1. Detecting and blocking prompt injections or system prompt override attacks.
    2. Classifying intent using structured domain taxonomies.
    3. Short-circuiting off-topic queries (e.g. 'What is the weather in Dallas?') with zero LLM token cost.
    4. Routing in-scope queries to the optimal specialist sub-engine.
    """

    INJECTION_PATTERNS = [
        r"(ignore|disregard|forget|override)\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|directives)",
        r"system\s*prompt\s*override",
        r"system:\s*(bypass|disregard|override)",
        r"(you\s+are\s+now\s+a\s+|enable\s+)(dan|developer|jailbroken|unrestricted)",
        r"(developer|dan|jailbreak)\s+mode",
        r"reveal\s+(your|the)\s+(system|secret)\s+(prompt|instructions|keys)",
        r"base64\s*decode.*bypass",
        r"roleplay\s+as\s+an\s+unconstrained"
    ]

    OUT_OF_SCOPE_PATTERNS = [
        r"\b(weather|forecast|temperature|rain|snow)\b",
        r"\b(recipe|cook|baking|dinner|lunch|breakfast)\b",
        r"\b(poem|poetry|song|lyrics|rap|haiku)\b",
        r"\b(movie|cinema|film|actor|hollywood|celebrity)\b",
        r"\b(sports|football|basketball|soccer|baseball|nba|nfl|score|world\s*cup|olympics|championship|super\s*bowl)\b",
        r"\b(who\s+won|who\s+is\s+president|capital\s+of|president\s+of)\b",
        r"\b(joke|riddle|funny|meme)\b",
        r"\b(horoscope|astrology|zodiac)\b",
        r"\b(flight|hotel|vacation|tourism|travel\s+tips)\b",
        r"\b(python\s+tutorial|write\s+a\s+game|tic-tac-toe)\b"
    ]

    FINANCIAL_DEEPDIVE_PATTERNS = [
        r"\b(arr|mrr|ebitda|gross\s+margin|operating\s+margin|cash\s+flow|burn\s+rate|runway)\b",
        r"\b(ltv|cac|payback|nrr|net\s+revenue\s+retention|churn|retention|cagr)\b",
        r"\b(dscr|walt|rent\s+roll|occupancy|sqft|price\s+per\s+sf|cam\s+reconciliation)\b"
    ]

    CAP_TABLE_PATTERNS = [
        r"\b(cap\s*table|waterfall|liquidation\s+preference|preferred\s+shares|common\s+stock)\b",
        r"\b(moic|irr|dilution|payout|exit\s+valuation|seniority|convertible\s+note)\b"
    ]

    DOCUMENT_REQUEST_PATTERNS = [
        r"\b(data\s*room|document\s+needed|request\s+document|missing\s+audit|qofe|offering\s+memo)\b",
        r"\b(due\s+diligence\s+checklist|audit\s+request|p&l\s+request)\b",
        r"\b(request|require|need|upload|missing)\b.*(financial|statement|audit|soc\s*2|report|document|agreement)"
    ]

    def validate_ingress_guardrails(self, query: str) -> IngressGuardrailResult:
        """
        Layer 1 Ingress Defense: Evaluates query for adversarial injection attempts.
        """
        query_clean = query.strip()
        flags = []

        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, query_clean, re.IGNORECASE):
                flags.append(f"INJECTION_PATTERN_MATCH: {pattern}")

        if flags:
            return IngressGuardrailResult(
                is_safe=False,
                sanitized_query="",
                blocked_reason="Prompt injection or system prompt override attempt detected.",
                flags=flags
            )

        return IngressGuardrailResult(
            is_safe=True,
            sanitized_query=query_clean,
            flags=[]
        )

    def inspect_ingress(self, query: str) -> IngressGuardrailResult:
        """Alias for validate_ingress_guardrails."""
        return self.validate_ingress_guardrails(query)

    def classify_intent(self, query: str) -> IntentClassificationResult:
        """
        Layer 2 Scope & Intent Routing:
        Classifies incoming query into UserIntent with confidence score and target node.
        """
        # Step 1: Guardrail check
        guardrail = self.validate_ingress_guardrails(query)
        if not guardrail.is_safe:
            return IntentClassificationResult(
                intent=UserIntent.PROMPT_INJECTION,
                confidence=0.99,
                is_in_scope=False,
                explanation="Adversarial prompt injection pattern detected.",
                suggested_action="BLOCK_AND_AUDIT_LOG",
                target_node=None
            )

        query_lower = query.lower()

        # Step 2: Out of scope short-circuit
        for pattern in self.OUT_OF_SCOPE_PATTERNS:
            if re.search(pattern, query_lower):
                return IntentClassificationResult(
                    intent=UserIntent.OUT_OF_SCOPE,
                    confidence=0.95,
                    is_in_scope=False,
                    explanation=f"Query matches non-diligence domain taxonomy ('{pattern}').",
                    suggested_action="SHORT_CIRCUIT_FAST_EXIT",
                    target_node=None
                )

        # Step 3: Cap Table & Waterfall Routing
        for pattern in self.CAP_TABLE_PATTERNS:
            if re.search(pattern, query_lower):
                return IntentClassificationResult(
                    intent=UserIntent.CAP_TABLE_WATERFALL,
                    confidence=0.92,
                    is_in_scope=True,
                    explanation="Query targets equity ownership, liquidation preferences, or waterfall returns.",
                    suggested_action="ROUTE_TO_WATERFALL_CALCULATOR",
                    target_node="waterfall_calculator"
                )

        # Step 4: Financial Metrics & Unit Economics
        for pattern in self.FINANCIAL_DEEPDIVE_PATTERNS:
            if re.search(pattern, query_lower):
                return IntentClassificationResult(
                    intent=UserIntent.FINANCIAL_DEEPDIVE,
                    confidence=0.93,
                    is_in_scope=True,
                    explanation="Query requires deterministic financial ratio calculations or metric audit.",
                    suggested_action="ROUTE_TO_FINANCIAL_ANALYST",
                    target_node="financial_analyst_node"
                )

        # Step 5: Document & Data Room requests
        for pattern in self.DOCUMENT_REQUEST_PATTERNS:
            if re.search(pattern, query_lower):
                return IntentClassificationResult(
                    intent=UserIntent.DOCUMENT_REQUEST,
                    confidence=0.90,
                    is_in_scope=True,
                    explanation="Query concerns missing due diligence materials or data room document requests.",
                    suggested_action="ROUTE_TO_DATA_ROOM_MANAGER",
                    target_node="data_room_service"
                )

        # Default fallback: General Due Diligence Q&A (In-Scope)
        return IntentClassificationResult(
            intent=UserIntent.DILIGENCE_QUERY,
            confidence=0.85,
            is_in_scope=True,
            explanation="General investment due diligence and evidence synthesis inquiry.",
            suggested_action="ROUTE_TO_RAG_SYNTHESIZER",
            target_node="rag_chat_synthesizer"
        )


intent_router_service = IntentRouterService()
