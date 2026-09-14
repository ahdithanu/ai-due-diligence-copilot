from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field

class ClaimType(str, Enum):
    FACT = "FACT"
    CALCULATION = "CALCULATION"
    INFERENCE = "INFERENCE"
    ASSUMPTION = "ASSUMPTION"
    UNRESOLVED_QUESTION = "UNRESOLVED_QUESTION"

class MaterialityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ExecutionState(str, Enum):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class JobType(str, Enum):
    DILIGENCE_RUN = "DILIGENCE_RUN"
    RERUN = "RE-RUN"
    RE_RUN = "RE-RUN"
    CANARY_TEST = "CANARY_TEST"

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class OnboardingStage(str, Enum):
    DISCOVER = "DISCOVER"
    CONFIGURE = "CONFIGURE"
    VALIDATE = "VALIDATE"
    EVALUATE = "EVALUATE"
    PILOT = "PILOT"
    OBSERVE = "OBSERVE"
    TUNE = "TUNE"
    ACCEPT = "ACCEPT"
    EXPAND = "EXPAND"

class DiligenceStatus(str, Enum):
    CREATED = "CREATED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    EVIDENCE_EXTRACTED = "EVIDENCE_EXTRACTED"
    SPECIALIST_DILIGENCE = "SPECIALIST_DILIGENCE"
    CROSS_EXAMINATION = "CROSS_EXAMINATION"
    INVESTMENT_COMMITTEE = "INVESTMENT_COMMITTEE"
    MEMO_GENERATED = "MEMO_GENERATED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DocumentType(str, Enum):
    PITCH_DECK = "PITCH_DECK"
    FINANCIAL_STATEMENT = "FINANCIAL_STATEMENT"
    OPERATING_METRICS = "OPERATING_METRICS"
    MARKET_RESEARCH = "MARKET_RESEARCH"
    CUSTOMER_INFO = "CUSTOMER_INFO"
    MANAGEMENT_MATERIAL = "MANAGEMENT_MATERIAL"
    OTHER = "OTHER"

class ModelTaskType(str, Enum):
    FAST_EXTRACTION = "FAST_EXTRACTION"
    DETERMINISTIC_MATH = "DETERMINISTIC_MATH"
    REASONING_SYNTHESIS = "REASONING_SYNTHESIS"
    CRITIC_AUDIT = "CRITIC_AUDIT"

class ModelRoutingPolicy(BaseModel):
    primary_provider: str
    primary_model: str
    fallback_provider: str
    fallback_model: str
    timeout_seconds: float = 30.0
    max_retries: int = 3
    circuit_breaker_threshold: int = 3

class ChaosSimulationConfig(BaseModel):
    inject_rate_limit: bool = False
    inject_latency_ms: int = 0
    inject_schema_corruption: bool = False
    target_node: Optional[str] = None

class CircuitBreakerStatus(BaseModel):
    provider: str
    state: str = "CLOSED"  # "CLOSED", "OPEN", "HALF_OPEN"
    failure_count: int = 0
    last_failure_timestamp: Optional[datetime] = None


class DocumentChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    char_count: int = 0

class EvidenceRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    chunk_id: str
    content: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 1.0
    claim_type: ClaimType = ClaimType.FACT
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FinancialMetricRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str  # e.g., ARR, Revenue_Growth, Gross_Margin
    value: float
    unit: str  # e.g., USD, percentage, ratio, months
    period: str  # e.g., Q4_2024, FY2023
    formula: str
    input_evidence_ids: List[str] = Field(default_factory=list)
    is_deterministic: bool = True
    confidence: float = 1.0

class ClaimNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    claim_type: ClaimType
    evidence_ids: List[str] = Field(default_factory=list)
    materiality: MaterialityLevel = MaterialityLevel.MEDIUM
    supporting_reasoning: str = ""

class ContradictionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    claim_a_id: str
    claim_b_id: str
    description: str
    materiality: MaterialityLevel = MaterialityLevel.HIGH
    status: str = "OPEN"  # OPEN, RESOLVED, WAITING_HUMAN_REVIEW

class DiligenceQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    reason_it_matters: str
    related_risk_or_thesis: str
    required_evidence: str
    materiality: MaterialityLevel = MaterialityLevel.HIGH
    priority: int = 1
    status: str = "OPEN"  # OPEN, ANSWERED, DEFERRED

class SpecialistAnalysis(BaseModel):
    domain: str  # e.g., Financial, Market, Competitive, Customer, Product, Risk, UnitEconomics
    summary: str = ""
    claims: List[ClaimNode] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    iteration_count: int = 0
    passed_evaluation: bool = False

class AgentEvaluationResult(BaseModel):
    evaluator_name: str
    target_node: str
    evidence_coverage_score: float = 0.0
    citation_correctness_score: float = 0.0
    logical_consistency_score: float = 0.0
    financial_correctness_score: float = 0.0
    completeness_score: float = 0.0
    overall_pass: bool = False
    critique_feedback: List[str] = Field(default_factory=list)

class ExecutionLogEntry(BaseModel):
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_name: str
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, INTERRUPTED
    input_summary: Dict[str, Any] = Field(default_factory=dict)
    output_summary: Dict[str, Any] = Field(default_factory=dict)
    model_name: Optional[str] = None
    token_usage: Dict[str, int] = Field(default_factory=dict)
    evaluation_result: Optional[AgentEvaluationResult] = None
    iteration: int = 0
    next_edge_selected: Optional[str] = None
    error_message: Optional[str] = None


class DeploymentConfig(BaseModel):
    deployment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_name: str
    deployment_name: str
    investment_strategy: str  # "growth_equity_saas" or "traditional_buyout"
    required_diligence_sections: List[str] = Field(default_factory=list)
    financial_thresholds: Dict[str, float] = Field(default_factory=dict)
    risk_thresholds: Dict[str, str] = Field(default_factory=dict)
    required_evidence_types: List[str] = Field(default_factory=list)
    evaluation_thresholds: Dict[str, float] = Field(default_factory=lambda: {"min_quality_score": 0.85, "max_iterations": 3.0})
    human_escalation_rules: List[str] = Field(default_factory=list)
    enabled_models: List[str] = Field(default_factory=list)
    model_roles: Dict[str, str] = Field(default_factory=dict)
    allowed_tools: List[str] = Field(default_factory=list)
    output_requirements: Dict[str, Any] = Field(default_factory=dict)
    custom_terminology: Dict[str, str] = Field(default_factory=dict)

class FailureDetails(BaseModel):
    failed_node: str
    error_type: str
    error_message: str
    retryable: bool = True
    last_successful_checkpoint_id: Optional[str] = None
    suggested_recovery_action: str = ""
    affected_artifacts: List[str] = Field(default_factory=list)

class CheckpointRecord(BaseModel):
    checkpoint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    deployment_id: str
    investment_id: str
    node_id: str
    graph_state_version: int = 1
    iteration_count: int = 0
    evaluation_results: Dict[str, Any] = Field(default_factory=dict)
    routing_decision: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ExecutionState = ExecutionState.RUNNING

class DiligenceState(BaseModel):
    investment_id: str
    company_name: str
    industry: str
    target_round: str
    check_size_usd: Optional[float] = None
    status: DiligenceStatus = DiligenceStatus.CREATED
    deployment_id: Optional[str] = None
    deployment_config: Optional[DeploymentConfig] = None
    execution_state: ExecutionState = ExecutionState.RUNNING
    failure_details: Optional[FailureDetails] = None
    checkpoint_history: List[CheckpointRecord] = Field(default_factory=list)
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    document_chunks: List[DocumentChunk] = Field(default_factory=list)
    evidence_records: List[EvidenceRecord] = Field(default_factory=list)
    financial_metrics: List[FinancialMetricRecord] = Field(default_factory=list)
    specialist_analyses: Dict[str, SpecialistAnalysis] = Field(default_factory=dict)
    risk_register: List[ClaimNode] = Field(default_factory=list)
    contradictions: List[ContradictionRecord] = Field(default_factory=list)
    open_questions: List[DiligenceQuestion] = Field(default_factory=list)
    assumptions: List[ClaimNode] = Field(default_factory=list)
    bull_case: Optional[str] = None
    bear_case: Optional[str] = None
    base_case: Optional[str] = None
    skeptic_critique: Optional[str] = None
    investment_thesis: Optional[str] = None
    recommendation: Optional[str] = None  # INVEST, PASS, CONDITIONAL_PASS
    confidence_score: Optional[float] = None
    memo_markdown: Optional[str] = None
    citations: Dict[str, List[str]] = Field(default_factory=dict)
    evaluations: List[AgentEvaluationResult] = Field(default_factory=list)
    iteration_counts: Dict[str, int] = Field(default_factory=dict)
    human_review_required: bool = False
    human_review_reasons: List[str] = Field(default_factory=list)
    execution_history: List[ExecutionLogEntry] = Field(default_factory=list)
    chat_history: List["ChatMessage"] = Field(default_factory=list)
    data_room_requests: List["DataRoomRequest"] = Field(default_factory=list)
    ic_audio_script: Optional["ICAudioScript"] = None
    teaser_markdown: Optional[str] = None


# API Request/Response Schemas
class CreateInvestmentRequest(BaseModel):
    company_name: str
    industry: str
    target_round: str
    check_size_usd: Optional[float] = None

class InvestmentResponse(BaseModel):
    investment_id: str
    company_name: str
    industry: str
    target_round: str
    check_size_usd: Optional[float] = None
    status: DiligenceStatus
    created_at: datetime
    document_count: int = 0
    evidence_count: int = 0

class KeyMetrics(BaseModel):
    arr: str = "N/A"
    gross_margin: str = "N/A"
    nrr: str = "N/A"
    ltv_cac: str = "N/A"
    runway: str = "N/A"

class DealComparisonItem(BaseModel):
    investment_id: str
    company_name: str
    industry: str
    target_round: str
    check_size_usd: Optional[float] = None
    status: DiligenceStatus
    recommendation: Optional[str] = "PENDING"
    confidence_score: Optional[float] = 0.0
    key_metrics: KeyMetrics
    dominant_risks: List[str] = Field(default_factory=list)

class InvestmentMemoResponse(BaseModel):
    id: str
    investment_id: str
    memo_markdown: str
    recommendation: str
    confidence_score: float
    created_at: datetime

class RedFlagSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"

class CompanyComparisonSummary(BaseModel):
    investment_id: str
    company_name: str
    industry: Optional[str] = "N/A"
    target_round: Optional[str] = "N/A"
    check_size_usd: Optional[float] = None
    status: DiligenceStatus = DiligenceStatus.CREATED
    arr: str = "N/A"
    nrr: str = "N/A"
    gross_margin: str = "N/A"
    runway: str = "N/A"
    ltv_cac: str = "N/A"
    moat_strength: str = "N/A"
    risk_count: int = 0
    recommendation: Optional[str] = "PENDING"
    confidence_score: Optional[float] = 0.0
    dominant_risks: List[str] = Field(default_factory=list)
    key_metrics: Optional[KeyMetrics] = None

    def model_post_init(self, __context: Any) -> None:
        if self.key_metrics is None:
            self.key_metrics = KeyMetrics(
                arr=self.arr,
                gross_margin=self.gross_margin,
                nrr=self.nrr,
                ltv_cac=self.ltv_cac,
                runway=self.runway
            )


class PortfolioComparisonResponse(BaseModel):
    companies: List[CompanyComparisonSummary] = Field(default_factory=list)
    total_companies: int = 0
    compared_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RedFlagAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    investment_id: str
    company_name: str
    category: str = "General"
    title: str
    description: str = ""
    severity: RedFlagSeverity = RedFlagSeverity.HIGH
    materiality: MaterialityLevel = MaterialityLevel.HIGH
    mitigation_suggestion: str = ""
    evidence_citation: str = ""
    mitigation_action: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def model_post_init(self, __context: Any) -> None:
        if not self.evidence_citation and self.description:
            self.evidence_citation = self.description
        elif not self.description and self.evidence_citation:
            self.description = self.evidence_citation

        if not self.mitigation_action and self.mitigation_suggestion:
            self.mitigation_action = self.mitigation_suggestion
        elif not self.mitigation_suggestion and self.mitigation_action:
            self.mitigation_suggestion = self.mitigation_action


class JobRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    investment_id: Optional[str] = None
    job_type: str = JobType.DILIGENCE_RUN.value
    status: str = JobStatus.QUEUED.value
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class PreflightCheckResult(BaseModel):
    check_name: str
    passed: bool
    details: str

class DeploymentReadinessReport(BaseModel):
    deployment_id: str
    status: str  # "READY", "READY_WITH_RISKS", "NOT_READY"
    checks: List[PreflightCheckResult] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CanaryResult(BaseModel):
    passed: bool
    synthetic_investment_id: str
    node_checkpoints_verified: int
    conflict_resolved: bool
    teardown_successful: bool
    duration_ms: float

class FDEObservabilityMetrics(BaseModel):
    request_error_rate: float
    graph_execution_failure_rate: float
    model_average_latency_ms: float
    total_model_cost_usd: float
    queue_depth: int
    checkpoint_failure_rate: float
    human_escalation_rate: float
    autonomous_completion_rate: float
    recovery_success_rate: float


class DemoStep(str, Enum):
    DEPLOYMENT_SELECTION = "DEPLOYMENT_SELECTION"
    DOCUMENT_FINANCIAL_ENGINE = "DOCUMENT_FINANCIAL_ENGINE"
    SPECIALIST_CRITIC_LOOP = "SPECIALIST_CRITIC_LOOP"
    CONTRADICTION_INTERRUPT = "CONTRADICTION_INTERRUPT"
    CHECKPOINT_RECOVERY = "CHECKPOINT_RECOVERY"
    IC_DEBATE_AND_MEMO = "IC_DEBATE_AND_MEMO"
    FAILURE_LAB_FAILOVER = "FAILURE_LAB_FAILOVER"
    ACCEPTANCE_AND_CANARY = "ACCEPTANCE_AND_CANARY"


class DemoControlRequest(BaseModel):
    speed: float = 1.0
    loop: bool = True


class DemoStatusResponse(BaseModel):
    active: bool
    paused: bool
    current_step: str
    current_step_name: str
    active_tab: str
    loop_count: int
    progress_pct: float
    auto_loop: bool
    speed: float
    log_messages: List[str] = Field(default_factory=list)


class CapTableEntry(BaseModel):
    share_class: str
    investor_name: str
    shares_held: float
    ownership_pct: float
    liquidation_preference_multiplier: float = 1.0
    is_participating: bool = False
    cap_multiplier: Optional[float] = None


class WaterfallPayout(BaseModel):
    share_class: str
    investor_name: str
    payout_usd: float
    moic: float
    irr_pct: Optional[float] = 0.0


class WaterfallScenario(BaseModel):
    exit_valuation_usd: float
    payouts: List[WaterfallPayout] = Field(default_factory=list)


class SensitivityScenario(BaseModel):
    scenario_name: str
    revenue_growth_delta_pct: float
    churn_delta_pct: float
    gross_margin_delta_pct: float
    cac_payback_delta_months: float
    resulting_runway_months: float
    resulting_ebitda_margin_pct: float
    risk_level: str


class SensitivityMatrix(BaseModel):
    base_runway_months: float
    base_ebitda_margin_pct: float
    scenarios: List[SensitivityScenario] = Field(default_factory=list)


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str
    content: str
    evidence_citations: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DataRoomRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    document_needed: str
    priority: str = "HIGH"
    status: str = "PENDING"
    rationale: str


class ICAudioScript(BaseModel):
    title: str
    duration_seconds: int = 180
    speakers: List[Dict[str, Any]] = Field(default_factory=list)
    transcript_lines: List[Dict[str, Any]] = Field(default_factory=list)


class WaterfallRequest(BaseModel):
    cap_table: Optional[List[CapTableEntry]] = None
    exit_valuation_usd: Optional[float] = 50_000_000.0
    total_investment_usd: Optional[float] = 10_000_000.0


class SensitivityRequest(BaseModel):
    financial_metrics: Optional[Dict[str, float]] = None


class ChatRequest(BaseModel):
    question: str


class RAGSearchResult(BaseModel):
    id: str
    document_name: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    snippet: str
    hybrid_score: float
    vector_score: float
    keyword_score: float
    confidence: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    min_hybrid_score: float = 0.0
    investment_id: Optional[str] = None


class RAGQueryResponse(BaseModel):
    results: List[RAGSearchResult]
    total_results: int
    query_time_ms: float
    top_k: int
    min_hybrid_score: float


# CISO & Enterprise Governance Schemas
class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    IC_PARTNER = "IC_PARTNER"
    DEAL_LEAD = "DEAL_LEAD"
    ANALYST = "ANALYST"
    EXTERNAL_LP_VIEWER = "EXTERNAL_LP_VIEWER"


class TenantContext(BaseModel):
    org_id: str
    org_name: str
    user_id: str
    user_email: str
    role: UserRole


class DLPScanRequest(BaseModel):
    text: Optional[str] = None
    input_text: Optional[str] = None


class KMSRevokeRequest(BaseModel):
    org_id: str


class DLPFinding(BaseModel):
    entity_type: str
    original_text: str
    redacted_token: str
    start_offset: int
    end_offset: int
    confidence_score: float = 1.0


class DLPScanResult(BaseModel):
    original_text: str
    sanitized_text: str
    redacted_entities_count: int = 0
    detected_entity_types: List[str] = Field(default_factory=list)
    is_clean: bool = True
    findings: List[DLPFinding] = Field(default_factory=list)
    redacted_text: Optional[str] = None
    scan_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Optional[str] = "CLEAN"


class AuditLogRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: str
    actor_role: str
    org_id: str
    action: str
    resource_type: str
    resource_id: str
    client_ip: str = "127.0.0.1"
    prev_hash: str = "0"
    entry_hash: str = ""
    chain_verified: bool = True


class KMSKeyRecord(BaseModel):
    key_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    org_id: str
    status: str = "ACTIVE"  # "ACTIVE", "REVOKED", "SHREDDED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    algorithm: str = "AES-256-GCM"
    alias: Optional[str] = None
    cmk_arn: Optional[str] = None
    last_rotated_at: Optional[datetime] = None


class SOC2Report(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    compliance_score_pct: float
    status: str
    controls_evaluated: int
    controls_passed: int
    details: Dict[str, Any] = Field(default_factory=dict)
    audit_period: Optional[str] = "2026-Q1/Q3 Continuous Monitoring"
    audit_readiness_status: Optional[str] = "Audit Ready"
    certifying_firm: Optional[str] = "Ernst & Young / CISO Enterprise Audit"
    controls: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))



