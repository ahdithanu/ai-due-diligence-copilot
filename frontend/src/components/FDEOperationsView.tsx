import React, { useState, useEffect } from 'react';
import {
  OnboardingStage,
  PreflightCheckResult,
  DeploymentReadinessReport,
  CanaryResult,
  FDEObservabilityMetrics
} from '../types';

interface CustomerDeploymentInfo {
  id: string;
  customerName: string;
  deploymentName: string;
  stage: OnboardingStage;
  leadFDE: string;
  targetRound: string;
  progressPct: number;
  lastUpdated: string;
  notes: string;
}

const INITIAL_CUSTOMERS: CustomerDeploymentInfo[] = [
  {
    id: 'dep-apex-01',
    customerName: 'Apex Capital Management',
    deploymentName: 'Apex Growth Fund II Workspace',
    stage: 'CONFIGURE',
    leadFDE: 'Elena Rostova (Principal FDE)',
    targetRound: 'Series B / C Tech Deals',
    progressPct: 60,
    lastUpdated: '10 mins ago',
    notes: 'Configuring custom LTV/CAC threshold limits and Gemini 1.5 Flash fast extraction routing.'
  },
  {
    id: 'dep-sequoia-02',
    customerName: 'Sequoia Growth Partners',
    deploymentName: 'Sequoia Late-Stage Tech Copilot',
    stage: 'DEPLOY',
    leadFDE: 'Marcus Chen (Staff FDE)',
    targetRound: 'Growth & Pre-IPO',
    progressPct: 80,
    lastUpdated: '1 hour ago',
    notes: 'Pre-flight inspection completed (READY). Preparing production canary runner.'
  },
  {
    id: 'dep-benchmark-03',
    customerName: 'Benchmark Venture Capital',
    deploymentName: 'Benchmark Early Stage Seed Node',
    stage: 'PILOT',
    leadFDE: 'Sarah Jenkins (FDE)',
    targetRound: 'Seed & Series A',
    progressPct: 40,
    lastUpdated: '3 hours ago',
    notes: 'Ingested 14 historical seed pitch decks to audit deterministic math accuracy.'
  },
  {
    id: 'dep-founders-04',
    customerName: 'Founders Fund Alpha',
    deploymentName: 'Founders DeepTech Multi-Tenant',
    stage: 'EXPAND',
    leadFDE: 'Alex Rivera (FDE Director)',
    targetRound: 'DeepTech & HardTech',
    progressPct: 100,
    lastUpdated: 'Yesterday',
    notes: 'Production rollout active across 12 partner accounts with automated IC memo synthesis.'
  }
];

const INITIAL_PREFLIGHT_CHECKS: PreflightCheckResult[] = [
  {
    id: 'chk-1',
    name: 'Database & State Migrations',
    category: 'migrations',
    passed: true,
    status: 'PASSED',
    details: 'Schema v2.4 applied cleanly. Backward compatibility verified across all 18 table constraints.',
    latency_ms: 42
  },
  {
    id: 'chk-2',
    name: 'Model Routing & Fallback Policies',
    category: 'model_routing',
    passed: true,
    status: 'PASSED',
    details: 'Gemini 1.5 Pro primary & GPT-4o fallback circuit breakers CLOSED. Health checks 100%.',
    latency_ms: 115
  },
  {
    id: 'chk-3',
    name: 'Checkpoint Persistence & Snapshotting',
    category: 'checkpoint_persistence',
    passed: true,
    status: 'PASSED',
    details: 'SQLite & Redis snapshotting operational. Automatic graph resumption verified.',
    latency_ms: 28
  },
  {
    id: 'chk-4',
    name: 'Failure Lab Baseline Audit',
    category: 'failure_lab',
    passed: true,
    status: 'PASSED',
    details: 'Synthetic chaos injection suite (429 Rate Limit, Latency Spike, Corrupted JSON) passed cleanly.',
    latency_ms: 195
  },
  {
    id: 'chk-5',
    name: 'Tenant Data Isolation & Security',
    category: 'tenant_isolation',
    passed: true,
    status: 'PASSED',
    details: 'Strict customer tenant space boundaries active. AES-256 encryption & TLS 1.3 verified.',
    latency_ms: 36
  }
];

const STAGE_ORDER: OnboardingStage[] = ['DISCOVER', 'PILOT', 'CONFIGURE', 'DEPLOY', 'EXPAND'];

const STAGE_DESCRIPTIONS: Record<OnboardingStage, { label: string; icon: string; desc: string }> = {
  DISCOVER: {
    label: '1. Discovery & Ingestion',
    icon: '🔍',
    desc: 'Map customer data sources, confidential pitch decks, and financial statement formats.'
  },
  PILOT: {
    label: '2. Pilot Benchmark Test',
    icon: '🧪',
    desc: 'Execute baseline diligence graph runs and audit deterministic metric calculation accuracy.'
  },
  CONFIGURE: {
    label: '3. Custom Configuration',
    icon: '⚙️',
    desc: 'Configure custom risk thresholds, model routing fallbacks, and tenant isolation policies.'
  },
  DEPLOY: {
    label: '4. Production Deployment',
    icon: '🚀',
    desc: 'Pass pre-flight inspection gate, execute automated canary tests, and activate tenant space.'
  },
  EXPAND: {
    label: '5. Multi-Team Expansion',
    icon: '📈',
    desc: 'Scale Copilot across deal teams, integrate IC memo generation, and enforce SLAs.'
  }
};

export const FDEOperationsView: React.FC = () => {
  // Active customer selection
  const [customers, setCustomers] = useState<CustomerDeploymentInfo[]>(INITIAL_CUSTOMERS);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>(INITIAL_CUSTOMERS[0].id);

  // Pre-flight Inspection State
  const [preflightChecks, setPreflightChecks] = useState<PreflightCheckResult[]>(INITIAL_PREFLIGHT_CHECKS);
  const [runningPreflight, setRunningPreflight] = useState<boolean>(false);
  const [simulatedRiskMode, setSimulatedRiskMode] = useState<boolean>(false);
  const [simulatedFailureMode, setSimulatedFailureMode] = useState<boolean>(false);

  // Canary State
  const [canaryResult, setCanaryResult] = useState<CanaryResult>({
    canary_id: 'canary-init',
    status: 'IDLE',
    synthetic_requests_sent: 0,
    synthetic_requests_passed: 0,
    error_rate_pct: 0,
    avg_latency_ms: 0,
    teardown_verified: true,
    log_output: ['System idle. Ready to launch post-deployment canary test.']
  });
  const [runningCanary, setRunningCanary] = useState<boolean>(false);

  // Observability Metrics State
  const [metrics, setMetrics] = useState<FDEObservabilityMetrics>({
    request_error_rate_pct: 0.14,
    model_latency_ms: 385,
    total_model_cost_usd: 1428.60,
    queue_depth: 2,
    autonomous_completion_rate_pct: 93.8,
    human_escalation_rate_pct: 6.2,
    recovery_success_rate_pct: 99.4
  });
  const [autoRefreshTelemetry, setAutoRefreshTelemetry] = useState<boolean>(true);

  // Dual loop visualizer active tab/focus
  const [selectedLoopNode, setSelectedLoopNode] = useState<'cicd' | 'onboarding'>('onboarding');

  const selectedCustomer = customers.find(c => c.id === selectedCustomerId) || customers[0];

  // Auto telemetry jitter
  useEffect(() => {
    if (!autoRefreshTelemetry) return;
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        request_error_rate_pct: parseFloat((0.10 + Math.random() * 0.10).toFixed(2)),
        model_latency_ms: Math.floor(360 + Math.random() * 50),
        total_model_cost_usd: parseFloat((prev.total_model_cost_usd + Math.random() * 0.15).toFixed(2)),
        queue_depth: Math.floor(1 + Math.random() * 4),
        autonomous_completion_rate_pct: parseFloat((93.5 + Math.random() * 1.0).toFixed(1)),
        human_escalation_rate_pct: parseFloat((5.5 + Math.random() * 1.0).toFixed(1)),
        recovery_success_rate_pct: parseFloat((99.1 + Math.random() * 0.8).toFixed(1))
      }));
    }, 4000);
    return () => clearInterval(interval);
  }, [autoRefreshTelemetry]);

  // Handler: Advance Stage
  const handleAdvanceStage = () => {
    setCustomers(prev =>
      prev.map(c => {
        if (c.id === selectedCustomerId) {
          const currentIndex = STAGE_ORDER.indexOf(c.stage);
          if (currentIndex < STAGE_ORDER.length - 1) {
            const nextStage = STAGE_ORDER[currentIndex + 1];
            const newProgress = Math.round(((currentIndex + 2) / STAGE_ORDER.length) * 100);
            return {
              ...c,
              stage: nextStage,
              progressPct: newProgress,
              lastUpdated: 'Just now',
              notes: `Advanced to ${nextStage} stage via FDE Hub controls.`
            };
          }
        }
        return c;
      })
    );
  };

  // Handler: Reset Customer Stage
  const handleResetStage = () => {
    setCustomers(prev =>
      prev.map(c => {
        if (c.id === selectedCustomerId) {
          return {
            ...c,
            stage: 'DISCOVER',
            progressPct: 20,
            lastUpdated: 'Just now',
            notes: 'Stage reset to DISCOVER for testing.'
          };
        }
        return c;
      })
    );
  };

  // Compute overall Preflight Readiness Status
  const getOverallReadinessStatus = (): 'READY' | 'READY_WITH_RISKS' | 'NOT_READY' => {
    if (preflightChecks.some(chk => chk.status === 'FAILED')) return 'NOT_READY';
    if (preflightChecks.some(chk => chk.status === 'WARNING')) return 'READY_WITH_RISKS';
    return 'READY';
  };

  // Handler: Run Preflight Inspection
  const handleRunPreflight = () => {
    setRunningPreflight(true);
    setTimeout(() => {
      const updated = INITIAL_PREFLIGHT_CHECKS.map(check => {
        if (simulatedFailureMode && check.category === 'failure_lab') {
          return {
            ...check,
            passed: false,
            status: 'FAILED' as const,
            details: 'FAIL: Synthetic chaos injection baseline failed due to injected model latency threshold violation (12.4s > 5.0s).'
          };
        }
        if (simulatedRiskMode && check.category === 'model_routing') {
          return {
            ...check,
            passed: true,
            status: 'WARNING' as const,
            details: 'WARNING: Primary model Gemini 1.5 Flash exhibiting elevated 429 rate limits. Automatic failover to GPT-4o active.'
          };
        }
        return {
          ...check,
          passed: true,
          status: 'PASSED' as const,
          latency_ms: Math.floor(20 + Math.random() * 120)
        };
      });
      setPreflightChecks(updated);
      setRunningPreflight(false);
    }, 1800);
  };

  // Handler: Run Canary Test Runner
  const handleRunCanary = () => {
    setRunningCanary(true);
    const canaryId = `canary-${Date.now().toString().slice(-4)}`;
    setCanaryResult({
      canary_id: canaryId,
      status: 'RUNNING',
      started_at: new Date().toLocaleTimeString(),
      synthetic_requests_sent: 0,
      synthetic_requests_passed: 0,
      error_rate_pct: 0,
      avg_latency_ms: 0,
      teardown_verified: false,
      log_output: [`[${new Date().toLocaleTimeString()}] 🚀 Initiating canary test runner for ${selectedCustomer.customerName}...`]
    });

    const logs: string[] = [
      `[${new Date().toLocaleTimeString()}] 🚀 Initiating canary test runner for ${selectedCustomer.customerName}...`
    ];

    setTimeout(() => {
      logs.push(`[${new Date().toLocaleTimeString()}] 📦 Provisioning isolated sandbox space for synthetic document chunks...`);
      setCanaryResult(prev => ({
        ...prev,
        synthetic_requests_sent: 12,
        synthetic_requests_passed: 12,
        avg_latency_ms: 180,
        log_output: [...logs]
      }));
    }, 1000);

    setTimeout(() => {
      logs.push(`[${new Date().toLocaleTimeString()}] ⚡ Executing 50 synthetic financial calculation & claim extraction nodes...`);
      logs.push(`[${new Date().toLocaleTimeString()}] 🛡️ Auditing model router fallback circuit breakers under synthetic load...`);
      setCanaryResult(prev => ({
        ...prev,
        synthetic_requests_sent: 35,
        synthetic_requests_passed: 35,
        avg_latency_ms: 215,
        log_output: [...logs]
      }));
    }, 2200);

    setTimeout(() => {
      logs.push(`[${new Date().toLocaleTimeString()}] 🧹 Executing teardown protocol: Deleting all synthetic chunks & graph checkpoints...`);
      logs.push(`[${new Date().toLocaleTimeString()}] ✅ Teardown verification complete. Zero state pollution detected in tenant workspace.`);
      logs.push(`[${new Date().toLocaleTimeString()}] 🏆 Canary test PASSED successfully (50/50 synthetic requests succeeded, 0% error rate).`);

      setCanaryResult({
        canary_id: canaryId,
        status: 'PASSED',
        started_at: new Date().toLocaleTimeString(),
        completed_at: new Date().toLocaleTimeString(),
        synthetic_requests_sent: 50,
        synthetic_requests_passed: 50,
        error_rate_pct: 0.0,
        avg_latency_ms: 205,
        teardown_verified: true,
        log_output: [...logs]
      });
      setRunningCanary(false);
    }, 3600);
  };

  const overallReadiness = getOverallReadinessStatus();

  return (
    <div className="space-y-8 pb-12">
      {/* Header Bar */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900/90 via-slate-900/50 to-indigo-950/40 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-3xl">🚀</span>
            <div>
              <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-3">
                Forward Deployed Engineering (FDE) Hub
                <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 font-mono font-semibold">
                  Dual-Loop Ops
                </span>
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Continuous Software CI/CD Engine & Customer Onboarding Lifecycle Operations Center
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end md:self-auto">
          <button
            onClick={() => setAutoRefreshTelemetry(!autoRefreshTelemetry)}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 border ${
              autoRefreshTelemetry
                ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80 shadow-md shadow-emerald-950/50'
                : 'bg-slate-900 text-slate-400 border-slate-800'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${autoRefreshTelemetry ? 'bg-emerald-400 animate-ping' : 'bg-slate-500'}`}></span>
            {autoRefreshTelemetry ? 'Telemetry Live' : 'Telemetry Paused'}
          </button>
        </div>
      </div>

      {/* 1. Enterprise FDE Metrics Dashboard */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold tracking-wider text-slate-300 uppercase flex items-center gap-2">
            <span>📊</span> Enterprise FDE Telemetry & SLA Observability
          </h2>
          <span className="text-xs text-slate-400 font-mono">P99 SLA Threshold: 99.0%</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
          {/* Card 1: Error Rate */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Error Rate</div>
            <div className="text-xl font-black text-emerald-400 mt-1 font-mono">{metrics.request_error_rate_pct}%</div>
            <div className="text-[10px] text-slate-400 mt-1 flex items-center gap-1 font-medium">
              <span className="text-emerald-400">↓ 0.04%</span> vs target &lt;0.5%
            </div>
          </div>

          {/* Card 2: Model Latency */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Model Latency</div>
            <div className="text-xl font-black text-indigo-400 mt-1 font-mono">{metrics.model_latency_ms} <span className="text-xs font-normal text-slate-400">ms</span></div>
            <div className="text-[10px] text-slate-400 mt-1 flex items-center gap-1 font-medium">
              <span className="text-emerald-400">P95 Optimal</span> (&lt;600ms)
            </div>
          </div>

          {/* Card 3: Model Cost */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Model Cost</div>
            <div className="text-xl font-black text-amber-400 mt-1 font-mono">${metrics.total_model_cost_usd.toLocaleString()}</div>
            <div className="text-[10px] text-slate-400 mt-1 font-medium text-amber-400/90">
              MTD LLM Router Spend
            </div>
          </div>

          {/* Card 4: Queue Depth */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Queue Depth</div>
            <div className="text-xl font-black text-cyan-400 mt-1 font-mono">{metrics.queue_depth} <span className="text-xs font-normal text-slate-400">tasks</span></div>
            <div className="text-[10px] text-slate-400 mt-1 font-medium text-emerald-400">
              Active Graph Workers
            </div>
          </div>

          {/* Card 5: Autonomous Rate */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Autonomous Rate</div>
            <div className="text-xl font-black text-emerald-300 mt-1 font-mono">{metrics.autonomous_completion_rate_pct}%</div>
            <div className="text-[10px] text-slate-400 mt-1 font-medium">
              Zero Human Gate Interventions
            </div>
          </div>

          {/* Card 6: Human Escalation */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Escalation Rate</div>
            <div className="text-xl font-black text-purple-400 mt-1 font-mono">{metrics.human_escalation_rate_pct}%</div>
            <div className="text-[10px] text-slate-400 mt-1 font-medium">
              Human Review Triggered
            </div>
          </div>

          {/* Card 7: Recovery Rate */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Recovery Success</div>
            <div className="text-xl font-black text-teal-400 mt-1 font-mono">{metrics.recovery_success_rate_pct}%</div>
            <div className="text-[10px] text-slate-400 mt-1 font-medium text-emerald-400">
              Self-Healing & Failover
            </div>
          </div>
        </div>
      </div>

      {/* 2. Dual-Loop Architecture Visualizer Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-950/80 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>🔄</span> Dual-Loop Operations Architecture
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Decoupling Core Software Development CI/CD from Forward Deployed Engineering Customer Onboarding
            </p>
          </div>

          <div className="flex items-center gap-2 bg-slate-900 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setSelectedLoopNode('onboarding')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                selectedLoopNode === 'onboarding'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Customer Loop Focus
            </button>
            <button
              onClick={() => setSelectedLoopNode('cicd')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                selectedLoopNode === 'cicd'
                  ? 'bg-cyan-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Software CI/CD Focus
            </button>
          </div>
        </div>

        {/* Dual Loop Diagram Visualizer */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative">
          {/* Loop A: Software CI/CD Engine Loop */}
          <div className={`p-5 rounded-xl border transition-all ${
            selectedLoopNode === 'cicd'
              ? 'border-cyan-500/60 bg-slate-900/90 shadow-lg shadow-cyan-950/30'
              : 'border-slate-800 bg-slate-900/40 hover:border-slate-700'
          }`}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse"></span>
                <h3 className="font-bold text-sm text-cyan-300 uppercase tracking-wide">
                  Loop A: Software CI/CD Engine Loop
                </h3>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 font-mono font-semibold">
                Core Engineering
              </span>
            </div>

            {/* Steps Flow */}
            <div className="space-y-3">
              <div className="grid grid-cols-5 gap-1.5 text-center">
                {[
                  { step: 'CODE', icon: '💻', desc: 'Graph Specs & Models' },
                  { step: 'BUILD', icon: '⚙️', desc: 'Typescript & PyTest' },
                  { step: 'EVAL', icon: '🧪', desc: 'Failure Lab Suite' },
                  { step: 'PROD', icon: '🚀', desc: 'Canary Test Gate' },
                  { step: 'ROLLBACK', icon: '🛡️', desc: 'Auto Recovery' }
                ].map((s, idx) => (
                  <div key={s.step} className="p-2 rounded-lg bg-slate-950 border border-slate-800 hover:border-cyan-500/40 transition-all group">
                    <div className="text-base mb-1">{s.icon}</div>
                    <div className="text-[11px] font-black text-cyan-300 font-mono">{s.step}</div>
                    <div className="text-[9px] text-slate-400 mt-1 line-clamp-1">{s.desc}</div>
                  </div>
                ))}
              </div>

              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-300 space-y-1.5">
                <div className="font-semibold text-cyan-400 flex items-center justify-between">
                  <span>Engine Invariants & Security Standards</span>
                  <span className="text-[10px] text-slate-400 font-mono">v2.4.0-stable</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Maintains core model routing fallback matrices, deterministic financial math assertion parsers, and graph state checkpoint persistence.
                </p>
              </div>
            </div>
          </div>

          {/* Loop B: Customer Onboarding Lifecycle Loop */}
          <div className={`p-5 rounded-xl border transition-all ${
            selectedLoopNode === 'onboarding'
              ? 'border-indigo-500/60 bg-slate-900/90 shadow-lg shadow-indigo-950/30'
              : 'border-slate-800 bg-slate-900/40 hover:border-slate-700'
          }`}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-indigo-400 animate-pulse"></span>
                <h3 className="font-bold text-sm text-indigo-300 uppercase tracking-wide">
                  Loop B: Customer Onboarding Loop
                </h3>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono font-semibold">
                FDE Field Ops
              </span>
            </div>

            {/* Steps Flow */}
            <div className="space-y-3">
              <div className="grid grid-cols-5 gap-1.5 text-center">
                {[
                  { step: 'DISCOVER', icon: '🔍', desc: 'Schema Mapping' },
                  { step: 'PILOT', icon: '📊', desc: 'Benchmark Diligence' },
                  { step: 'CONFIGURE', icon: '⚙️', desc: 'Risk & Fallbacks' },
                  { step: 'DEPLOY', icon: '🏁', desc: 'Pre-flight Gate' },
                  { step: 'EXPAND', icon: '📈', desc: 'Multi-Tenant Scale' }
                ].map((s) => (
                  <div key={s.step} className="p-2 rounded-lg bg-slate-950 border border-slate-800 hover:border-indigo-500/40 transition-all">
                    <div className="text-base mb-1">{s.icon}</div>
                    <div className="text-[11px] font-black text-indigo-300 font-mono">{s.step}</div>
                    <div className="text-[9px] text-slate-400 mt-1 line-clamp-1">{s.desc}</div>
                  </div>
                ))}
              </div>

              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-300 space-y-1.5">
                <div className="font-semibold text-indigo-400 flex items-center justify-between">
                  <span>Forward Deployed Engineer (FDE) Workflow</span>
                  <span className="text-[10px] text-emerald-400 font-mono">4 Tenants Active</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  FDEs configure tenant-specific diligence thresholds, manage document chunking pipelines, and enforce zero-leakage security boundaries.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Customer Onboarding Stage Tracker Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-950/80 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>🎯</span> Customer Onboarding Stage Tracker
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Interactive FDE deployment stage manager and customer lifecycle progression
            </p>
          </div>

          {/* Customer Dropdown / Selector */}
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-400">Select Customer:</span>
            <select
              value={selectedCustomerId}
              onChange={(e) => setSelectedCustomerId(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2 font-semibold focus:outline-none focus:border-indigo-500"
            >
              {customers.map(c => (
                <option key={c.id} value={c.id}>
                  {c.customerName} ({c.stage})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Customer Header Info */}
        <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h3 className="font-extrabold text-base text-white">{selectedCustomer.customerName}</h3>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono font-bold">
                {selectedCustomer.deploymentName}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Lead FDE: <span className="text-slate-200 font-medium">{selectedCustomer.leadFDE}</span> • Target: <span className="text-slate-200 font-medium">{selectedCustomer.targetRound}</span>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-xs font-semibold text-slate-400">Stage Progress</div>
              <div className="text-lg font-black text-indigo-400 font-mono">{selectedCustomer.progressPct}%</div>
            </div>

            <button
              onClick={handleAdvanceStage}
              disabled={selectedCustomer.stage === 'EXPAND'}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                selectedCustomer.stage === 'EXPAND'
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                  : 'bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white shadow-lg shadow-indigo-600/30 active:scale-95'
              }`}
            >
              <span>Advance Stage</span>
              <span>&rarr;</span>
            </button>

            <button
              onClick={handleResetStage}
              className="px-3 py-2 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-400 border border-slate-800 transition-all"
              title="Reset customer stage to DISCOVER for testing"
            >
              ↺ Reset
            </button>
          </div>
        </div>

        {/* Stepper Component */}
        <div className="relative py-4">
          {/* Progress Connecting Line */}
          <div className="absolute top-1/2 left-6 right-6 h-1 bg-slate-800 -translate-y-1/2 z-0 hidden sm:block"></div>

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-4 relative z-10">
            {STAGE_ORDER.map((stageKey, idx) => {
              const currentStageIndex = STAGE_ORDER.indexOf(selectedCustomer.stage);
              const isCompleted = idx < currentStageIndex;
              const isCurrent = idx === currentStageIndex;
              const isUpcoming = idx > currentStageIndex;
              const info = STAGE_DESCRIPTIONS[stageKey];

              return (
                <div
                  key={stageKey}
                  className={`p-4 rounded-xl border transition-all ${
                    isCurrent
                      ? 'bg-indigo-950/80 border-indigo-500 shadow-xl shadow-indigo-950/50 ring-2 ring-indigo-500/40'
                      : isCompleted
                      ? 'bg-slate-900/90 border-emerald-600/50'
                      : 'bg-slate-950/60 border-slate-800 opacity-60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xl">{info.icon}</span>
                    {isCompleted ? (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono font-bold">
                        ✓ Done
                      </span>
                    ) : isCurrent ? (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500 text-white font-mono font-extrabold animate-pulse">
                        Active Stage
                      </span>
                    ) : (
                      <span className="text-xs text-slate-400 font-mono">Upcoming</span>
                    )}
                  </div>

                  <div className={`text-xs font-extrabold font-mono ${isCurrent ? 'text-indigo-300' : isCompleted ? 'text-emerald-300' : 'text-slate-400'}`}>
                    {stageKey}
                  </div>
                  <div className="text-[11px] font-semibold text-slate-200 mt-1 line-clamp-1">
                    {info.label.split('. ')[1]}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1.5 leading-snug">
                    {info.desc}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Stage Notes / Log info */}
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-400 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-indigo-400 font-bold">Latest FDE Note:</span>
            <span className="text-slate-300 font-mono text-[11px]">{selectedCustomer.notes}</span>
          </div>
          <span className="text-[10px] text-slate-400">{selectedCustomer.lastUpdated}</span>
        </div>
      </div>

      {/* 4. Deployment Acceptance Gate Panel */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-950/80 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>🛡️</span> Deployment Acceptance Gate Panel
              </h2>
              {/* Overall Status Badge */}
              <span className={`px-3 py-1 rounded-full text-xs font-black tracking-wider uppercase border font-mono ${
                overallReadiness === 'READY'
                  ? 'bg-emerald-950 text-emerald-300 border-emerald-700 shadow-md shadow-emerald-950/50'
                  : overallReadiness === 'READY_WITH_RISKS'
                  ? 'bg-amber-950 text-amber-300 border-amber-700 shadow-md shadow-amber-950/50'
                  : 'bg-rose-950 text-rose-300 border-rose-700 shadow-md shadow-rose-950/50'
              }`}>
                ● {overallReadiness === 'READY' ? 'READY (Green Gate)' : overallReadiness === 'READY_WITH_RISKS' ? 'READY WITH RISKS (Yellow)' : 'NOT READY (Red Gate)'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Automated pre-flight inspection report card for <span className="text-indigo-300 font-semibold">{selectedCustomer.customerName}</span>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleRunPreflight}
              disabled={runningPreflight}
              className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {runningPreflight ? (
                <>
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  <span>Running Inspection...</span>
                </>
              ) : (
                <>
                  <span>Run Pre-flight Inspection</span>
                </>
              )}
            </button>

            {/* Toggle options to demonstrate Yellow/Red state */}
            <button
              onClick={() => setSimulatedRiskMode(!simulatedRiskMode)}
              className={`px-3 py-2 rounded-xl text-xs font-semibold border transition-all ${
                simulatedRiskMode
                  ? 'bg-amber-950/80 text-amber-300 border-amber-700'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              Simulate Risk (Yellow)
            </button>
            <button
              onClick={() => setSimulatedFailureMode(!simulatedFailureMode)}
              className={`px-3 py-2 rounded-xl text-xs font-semibold border transition-all ${
                simulatedFailureMode
                  ? 'bg-rose-950/80 text-rose-300 border-rose-700'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              Simulate Failure (Red)
            </button>
          </div>
        </div>

        {/* Individual Check Items List */}
        <div className="space-y-3">
          {preflightChecks.map((check) => (
            <div
              key={check.id}
              className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                check.status === 'PASSED'
                  ? 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  : check.status === 'WARNING'
                  ? 'bg-amber-950/30 border-amber-800/80'
                  : 'bg-rose-950/30 border-rose-800/80'
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-sm text-white">{check.name}</span>
                  <span className="text-[10px] font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-950 border border-slate-800 uppercase">
                    {check.category}
                  </span>
                </div>
                <p className="text-xs text-slate-300 font-sans">{check.details}</p>
              </div>

              <div className="flex items-center gap-3 self-end sm:self-center">
                {check.latency_ms && (
                  <span className="text-[11px] font-mono text-slate-400">{check.latency_ms}ms</span>
                )}
                <span
                  className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold border ${
                    check.status === 'PASSED'
                      ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                      : check.status === 'WARNING'
                      ? 'bg-amber-950 text-amber-400 border-amber-800'
                      : 'bg-rose-950 text-rose-400 border-rose-800'
                  }`}
                >
                  {check.status === 'PASSED' ? '✓ PASSED' : check.status === 'WARNING' ? '⚠️ WARNING' : '❌ FAILED'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. Automated Canary Test Runner Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-950/80 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>🐣</span> Automated Canary Test Runner
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Synthetic end-to-end post-deployment verification with automatic artifact teardown
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Teardown Verification Badge */}
            <div className={`px-3 py-1.5 rounded-xl border text-xs font-mono font-bold flex items-center gap-2 ${
              canaryResult.teardown_verified
                ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800/90 shadow-md shadow-emerald-950/50'
                : 'bg-slate-900 text-slate-400 border-slate-800'
            }`}>
              <span>🛡️</span>
              <span>Teardown: {canaryResult.teardown_verified ? 'VERIFIED CLEAN' : 'PENDING'}</span>
            </div>

            <button
              onClick={handleRunCanary}
              disabled={runningCanary}
              className="px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-lg shadow-emerald-600/30 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {runningCanary ? (
                <>
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  <span>Executing Canary Suite...</span>
                </>
              ) : (
                <>
                  <span>Run Post-Deployment Canary</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Canary Metrics Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-[11px] font-semibold text-slate-400">Synthetic Requests</div>
            <div className="text-lg font-black text-white font-mono mt-0.5">
              {canaryResult.synthetic_requests_passed} / {canaryResult.synthetic_requests_sent}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-[11px] font-semibold text-slate-400">Canary Error Rate</div>
            <div className="text-lg font-black text-emerald-400 font-mono mt-0.5">
              {canaryResult.error_rate_pct}%
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-[11px] font-semibold text-slate-400">Synthetic Latency</div>
            <div className="text-lg font-black text-indigo-400 font-mono mt-0.5">
              {canaryResult.avg_latency_ms} ms
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-[11px] font-semibold text-slate-400">State Teardown</div>
            <div className="text-lg font-black text-teal-300 font-mono mt-0.5">
              {canaryResult.teardown_verified ? 'Zero Pollution' : 'Unverified'}
            </div>
          </div>
        </div>

        {/* Live Status Console / Stream Box */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Canary Execution Stream Log</span>
            <span>ID: {canaryResult.canary_id}</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 h-44 overflow-y-auto space-y-1.5 scrollbar-thin">
            {canaryResult.log_output.map((line, idx) => (
              <div
                key={idx}
                className={
                  line.includes('PASSED') || line.includes('complete') || line.includes('✅')
                    ? 'text-emerald-400 font-semibold'
                    : line.includes('Initiating') || line.includes('🚀')
                    ? 'text-cyan-300'
                    : 'text-slate-300'
                }
              >
                {line}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
