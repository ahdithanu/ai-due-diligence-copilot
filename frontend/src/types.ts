export type DiligenceStatus = 
  | 'CREATED'
  | 'DOCUMENT_UPLOADED'
  | 'EVIDENCE_EXTRACTED'
  | 'SPECIALIST_DILIGENCE'
  | 'CROSS_EXAMINATION'
  | 'INVESTMENT_COMMITTEE'
  | 'MEMO_GENERATED'
  | 'HUMAN_REVIEW'
  | 'COMPLETED'
  | 'FAILED';

export interface InvestmentSummary {
  investment_id: string;
  company_name: string;
  industry: string;
  target_round: string;
  check_size_usd?: number;
  status: DiligenceStatus;
  created_at: string;
  document_count: number;
  evidence_count: number;
}

export type ClaimType = 'FACT' | 'CALCULATION' | 'INFERENCE' | 'ASSUMPTION' | 'UNRESOLVED_QUESTION';
export type MaterialityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  page_number?: number;
  section_title?: string;
  char_count: number;
}

export interface EvidenceRecord {
  id: string;
  document_id: string;
  chunk_id: string;
  content: string;
  page_number?: number;
  section_title?: string;
  extracted_at: string;
  confidence: number;
  claim_type: ClaimType;
  metadata?: Record<string, any>;
}

export interface FinancialMetricRecord {
  id: string;
  metric_name: string;
  value: number;
  unit: string;
  period: string;
  formula: string;
  input_evidence_ids: string[];
  is_deterministic: boolean;
  confidence: number;
}

export interface ClaimNode {
  id: string;
  text: string;
  claim_type: ClaimType;
  evidence_ids: string[];
  materiality: MaterialityLevel;
  supporting_reasoning?: string;
}

export interface ContradictionRecord {
  id: string;
  claim_a_id: string;
  claim_b_id: string;
  description: string;
  materiality: MaterialityLevel;
  status: string;
}

export interface DiligenceQuestion {
  id: string;
  question: string;
  reason_it_matters: string;
  related_risk_or_thesis: string;
  required_evidence: string;
  materiality: MaterialityLevel;
  priority: number;
  status: string;
}

export interface SpecialistAnalysis {
  domain: string;
  summary: string;
  claims: ClaimNode[];
  strengths: string[];
  concerns: string[];
  confidence_score: number;
  iteration_count: number;
  passed_evaluation: boolean;
}

export interface AgentEvaluationResult {
  evaluator_name: string;
  target_node: string;
  evidence_coverage_score: number;
  citation_correctness_score: number;
  logical_consistency_score: number;
  financial_correctness_score: number;
  completeness_score: number;
  overall_pass: boolean;
  critique_feedback: string[];
}

export interface ExecutionLogEntry {
  execution_id: string;
  node_name: string;
  start_time: string;
  end_time?: string;
  status: string; // PENDING, RUNNING, COMPLETED, FAILED, INTERRUPTED
  input_summary?: Record<string, any>;
  output_summary?: Record<string, any>;
  model_name?: string;
  token_usage?: Record<string, number>;
  evaluation_result?: AgentEvaluationResult;
  iteration: number;
  next_edge_selected?: string;
  error_message?: string;
}

export type ExecutionState = 'RUNNING' | 'PAUSED' | 'FAILED' | 'WAITING_FOR_HUMAN' | 'COMPLETED' | 'CANCELLED';

export interface DeploymentConfig {
  deployment_id: string;
  customer_name: string;
  deployment_name: string;
  investment_strategy: string;
  required_diligence_sections?: string[];
  financial_thresholds?: Record<string, number>;
  risk_thresholds?: Record<string, string>;
  required_evidence_types?: string[];
  evaluation_thresholds?: Record<string, number>;
  human_escalation_rules?: string[];
  enabled_models?: string[];
  model_roles?: Record<string, string>;
  allowed_tools?: string[];
  output_requirements?: Record<string, any>;
  custom_terminology?: Record<string, string>;
}

export interface FailureDetails {
  failed_node: string;
  error_type: string;
  error_message: string;
  retryable?: boolean;
  last_successful_checkpoint_id?: string;
  suggested_recovery_action?: string;
  affected_artifacts?: string[];
  conflicting_evidence?: Array<{
    id: string;
    source_a: string;
    source_b: string;
    claim_a: string;
    claim_b: string;
    description: string;
  }>;
}

export interface CheckpointRecord {
  checkpoint_id: string;
  execution_id: string;
  deployment_id: string;
  investment_id: string;
  node_id: string;
  graph_state_version: number;
  iteration_count: number;
  evaluation_results?: Record<string, any>;
  routing_decision: string;
  timestamp: string;
  status: ExecutionState;
}

export interface DiligenceState {
  investment_id: string;
  company_name: string;
  industry: string;
  target_round: string;
  check_size_usd?: number;
  status: DiligenceStatus;
  deployment_id?: string;
  deployment_config?: DeploymentConfig;
  execution_state?: ExecutionState;
  failure_details?: FailureDetails;
  checkpoint_history?: CheckpointRecord[];
  documents: Array<Record<string, any>>;
  document_chunks: DocumentChunk[];
  evidence_records: EvidenceRecord[];
  financial_metrics: FinancialMetricRecord[];
  specialist_analyses: Record<string, SpecialistAnalysis>;
  risk_register: ClaimNode[];
  contradictions: ContradictionRecord[];
  open_questions: DiligenceQuestion[];
  assumptions: ClaimNode[];
  bull_case?: string;
  bear_case?: string;
  base_case?: string;
  skeptic_critique?: string;
  investment_thesis?: string;
  recommendation?: string; // INVEST, PASS, CONDITIONAL_PASS
  confidence_score?: number;
  memo_markdown?: string;
  citations: Record<string, string[]>;
  evaluations: AgentEvaluationResult[];
  iteration_counts: Record<string, number>;
  human_review_required: boolean;
  human_review_reasons: string[];
  execution_history: ExecutionLogEntry[];
}

export interface KeyMetrics {
  arr: string;
  gross_margin: string;
  nrr: string;
  ltv_cac: string;
  runway: string;
}

export interface DealComparisonItem {
  investment_id: string;
  company_name: string;
  industry: string;
  target_round: string;
  check_size_usd?: number;
  status: DiligenceStatus;
  recommendation?: string;
  confidence_score?: number;
  key_metrics: KeyMetrics;
  dominant_risks: string[];
}

export interface RedFlagAlert {
  id: string;
  investment_id: string;
  company_name: string;
  title: string;
  severity: MaterialityLevel;
  category: string;
  evidence_citation: string;
  mitigation_action: string;
  created_at: string;
}

export type ModelTaskType = 'FAST_EXTRACTION' | 'DETERMINISTIC_MATH' | 'REASONING_SYNTHESIS' | 'CRITIC_AUDIT';

export interface ModelRoutingPolicy {
  primary_provider: string;
  primary_model: string;
  fallback_provider: string;
  fallback_model: string;
  timeout_seconds: number;
  max_retries: number;
  circuit_breaker_threshold: number;
}

export interface ChaosSimulationConfig {
  inject_rate_limit: boolean;
  inject_latency_ms: number;
  inject_schema_corruption: boolean;
  target_node?: string | null;
}

export interface CircuitBreakerStatus {
  provider: string;
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  failure_count: number;
  last_failure_timestamp?: string | null;
}

export interface FailoverEvent {
  id: string;
  timestamp: string;
  node_name: string;
  task_type: ModelTaskType;
  primary_provider: string;
  primary_model: string;
  error_message: string;
  fallback_provider: string;
  fallback_model: string;
  status: 'SUCCESS' | 'FAILED';
}

export type OnboardingStage = 'DISCOVER' | 'PILOT' | 'CONFIGURE' | 'DEPLOY' | 'EXPAND';

export interface PreflightCheckResult {
  id: string;
  name: string;
  category: 'migrations' | 'model_routing' | 'checkpoint_persistence' | 'failure_lab' | 'tenant_isolation' | string;
  passed: boolean;
  status: 'PASSED' | 'WARNING' | 'FAILED';
  details: string;
  latency_ms?: number;
}

export interface DeploymentReadinessReport {
  deployment_id: string;
  customer_name: string;
  overall_status: 'READY' | 'READY_WITH_RISKS' | 'NOT_READY';
  timestamp: string;
  checks: PreflightCheckResult[];
  risk_summary?: string[];
  blockers?: string[];
}

export interface CanaryResult {
  canary_id: string;
  status: 'IDLE' | 'RUNNING' | 'PASSED' | 'FAILED';
  started_at?: string;
  completed_at?: string;
  synthetic_requests_sent: number;
  synthetic_requests_passed: number;
  error_rate_pct: number;
  avg_latency_ms: number;
  teardown_verified: boolean;
  log_output: string[];
}

export interface FDEObservabilityMetrics {
  request_error_rate_pct: number;
  model_latency_ms: number;
  total_model_cost_usd: number;
  queue_depth: number;
  autonomous_completion_rate_pct: number;
  human_escalation_rate_pct: number;
  recovery_success_rate_pct: number;
}
export type DemoStep =
  | 'DEPLOYMENT_SELECTION'
  | 'DOCUMENT_FINANCIAL_ENGINE'
  | 'SPECIALIST_CRITIC_LOOP'
  | 'CONTRADICTION_INTERRUPT'
  | 'CHECKPOINT_RECOVERY'
  | 'IC_DEBATE_AND_MEMO'
  | 'FAILURE_LAB_FAILOVER'
  | 'ACCEPTANCE_AND_CANARY';

export interface DemoControlRequest {
  speed?: number;
  loop?: boolean;
}

export interface DemoStatusResponse {
  active: boolean;
  paused: boolean;
  current_step: DemoStep | string;
  current_step_name: string;
  active_tab: string;
  loop_count: number;
  progress_pct: number;
  auto_loop: boolean;
  speed: number;
  log_messages: string[];
}

export interface CapTableEntry {
  id: string;
  shareholder_name: string;
  share_class: 'Founders Common' | 'Employee Options' | 'Seed Preferred' | 'Series A Preferred' | 'Series B Preferred' | string;
  shares: number;
  ownership_pct: number;
  investment_usd: number;
  liquidation_preference_multiplier: number;
  seniority: number;
  participating: boolean;
  participation_cap_multiplier?: number;
}

export interface WaterfallScenarioPayout {
  share_class: string;
  shareholder_name?: string;
  preference_payout_usd: number;
  common_payout_usd: number;
  total_payout_usd: number;
  moic: number;
  return_pct: number;
  effective_ownership_pct: number;
}

export interface WaterfallScenario {
  id: string;
  exit_valuation_usd: number;
  payouts: WaterfallScenarioPayout[];
  common_total_usd: number;
  preferred_total_usd: number;
  created_at: string;
}

export interface SensitivityMatrixCell {
  burn_delta_pct: number;
  growth_delta_pct: number;
  effective_burn_usd: number;
  effective_arr_growth_pct: number;
  runway_months: number;
  runway_compression_pct: number;
  alert_level: 'HEALTHY' | 'MODERATE' | 'CRITICAL';
}

export interface SensitivityMatrix {
  id: string;
  base_arr_usd: number;
  base_burn_rate_monthly_usd: number;
  base_cash_usd: number;
  base_runway_months: number;
  burn_rate_steps_pct: number[];
  growth_rate_steps_pct: number[];
  matrix: SensitivityMatrixCell[][];
}

export interface Citation {
  source_id: string;
  document_name: string;
  page_number?: number;
  section_title?: string;
  snippet: string;
  relevance_score: number;
  claim_type?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: string;
  citations?: Citation[];
  suggested_followups?: string[];
  is_thinking?: boolean;
}

export interface DataRoomRequest {
  id: string;
  title: string;
  category: 'Financials' | 'Legal' | 'Technical' | 'Customer' | 'Compliance' | string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'OPEN' | 'IN_PROGRESS' | 'FULFILLED' | 'REJECTED';
  requested_by: string;
  reason_it_matters: string;
  suggested_item?: string;
  created_at: string;
}

export interface ICAudioSpeaker {
  role: 'Bull' | 'Bear' | 'Skeptic';
  name: string;
  avatar_color: 'green' | 'red' | 'yellow';
  title: string;
}

export interface ICAudioTurn {
  id: string;
  speaker: 'Bull' | 'Bear' | 'Skeptic';
  speaker_name: string;
  avatar_color: 'green' | 'red' | 'yellow';
  start_time_sec: number;
  end_time_sec: number;
  text: string;
  key_point?: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
}

export interface ICAudioScript {
  id: string;
  title: string;
  total_duration_sec: number;
  summary: string;
  speakers: ICAudioSpeaker[];
  turns: ICAudioTurn[];
}
