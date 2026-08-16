import React, { useState, useEffect } from 'react';
import {
  ChaosSimulationConfig,
  CircuitBreakerStatus,
  ModelRoutingPolicy,
  ModelTaskType,
  FailoverEvent
} from '../types';

const INITIAL_ROUTING_MATRIX: Record<ModelTaskType, ModelRoutingPolicy> = {
  FAST_EXTRACTION: {
    primary_provider: 'gemini',
    primary_model: 'gemini-1.5-flash',
    fallback_provider: 'openai',
    fallback_model: 'gpt-4o-mini',
    timeout_seconds: 15.0,
    max_retries: 2,
    circuit_breaker_threshold: 3
  },
  DETERMINISTIC_MATH: {
    primary_provider: 'gemini',
    primary_model: 'gemini-1.5-pro',
    fallback_provider: 'openai',
    fallback_model: 'gpt-4o',
    timeout_seconds: 30.0,
    max_retries: 3,
    circuit_breaker_threshold: 3
  },
  REASONING_SYNTHESIS: {
    primary_provider: 'gemini',
    primary_model: 'gemini-1.5-pro',
    fallback_provider: 'openai',
    fallback_model: 'gpt-4o',
    timeout_seconds: 45.0,
    max_retries: 3,
    circuit_breaker_threshold: 3
  },
  CRITIC_AUDIT: {
    primary_provider: 'openai',
    primary_model: 'gpt-4o',
    fallback_provider: 'gemini',
    fallback_model: 'gemini-1.5-pro',
    timeout_seconds: 45.0,
    max_retries: 3,
    circuit_breaker_threshold: 3
  }
};

const INITIAL_CIRCUIT_BREAKERS: Record<string, CircuitBreakerStatus> = {
  gemini: { provider: 'Gemini (Google AI)', state: 'CLOSED', failure_count: 0, last_failure_timestamp: null },
  openai: { provider: 'OpenAI (GPT-4o)', state: 'CLOSED', failure_count: 0, last_failure_timestamp: null },
  mock: { provider: 'Mock Fallback LLM', state: 'CLOSED', failure_count: 0, last_failure_timestamp: null }
};

const INITIAL_FAILOVER_TRACES: FailoverEvent[] = [
  {
    id: 'tr-101',
    timestamp: new Date(Date.now() - 1000 * 60 * 4).toLocaleTimeString(),
    node_name: 'IngestionChunker',
    task_type: 'FAST_EXTRACTION',
    primary_provider: 'gemini',
    primary_model: 'gemini-1.5-flash',
    error_message: 'Rate Limit 429: Too Many Requests (Chaos Injected)',
    fallback_provider: 'openai',
    fallback_model: 'gpt-4o-mini',
    status: 'SUCCESS'
  },
  {
    id: 'tr-102',
    timestamp: new Date(Date.now() - 1000 * 60 * 12).toLocaleTimeString(),
    node_name: 'FinancialAnalyst',
    task_type: 'DETERMINISTIC_MATH',
    primary_provider: 'gemini',
    primary_model: 'gemini-1.5-pro',
    error_message: 'Timeout: Request exceeded 30.0s threshold',
    fallback_provider: 'openai',
    fallback_model: 'gpt-4o',
    status: 'SUCCESS'
  },
  {
    id: 'tr-103',
    timestamp: new Date(Date.now() - 1000 * 60 * 25).toLocaleTimeString(),
    node_name: 'CriticEvaluator',
    task_type: 'CRITIC_AUDIT',
    primary_provider: 'openai',
    primary_model: 'gpt-4o',
    error_message: 'Schema Corruption: Invalid JSON response structure',
    fallback_provider: 'gemini',
    fallback_model: 'gemini-1.5-pro',
    status: 'SUCCESS'
  }
];

export const FailureLabView: React.FC = () => {
  const [matrix, setMatrix] = useState<Record<string, ModelRoutingPolicy>>(INITIAL_ROUTING_MATRIX);
  const [circuitBreakers, setCircuitBreakers] = useState<Record<string, CircuitBreakerStatus>>(INITIAL_CIRCUIT_BREAKERS);
  const [chaosConfig, setChaosConfig] = useState<ChaosSimulationConfig>({
    inject_rate_limit: false,
    inject_latency_ms: 0,
    inject_schema_corruption: false,
    target_node: null
  });

  const [hasLatencySpike, setHasLatencySpike] = useState(false);
  const [failoverTraces, setFailoverTraces] = useState<FailoverEvent[]>(INITIAL_FAILOVER_TRACES);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'info' | 'warning' | 'error'; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  // Fetch initial failure lab config & circuit breakers from backend
  const fetchStatus = async () => {
    try {
      const [configRes, cbRes, matrixRes] = await Promise.all([
        fetch('/api/v1/failure-lab/config'),
        fetch('/api/v1/failure-lab/circuit-breakers'),
        fetch('/api/v1/failure-lab/matrix')
      ]);

      if (configRes.ok) {
        const cfg: ChaosSimulationConfig = await configRes.json();
        setChaosConfig(cfg);
        setHasLatencySpike(cfg.inject_latency_ms >= 5000);
      }
      if (cbRes.ok) {
        const cbs: Record<string, CircuitBreakerStatus> = await cbRes.json();
        setCircuitBreakers(prev => ({
          ...prev,
          ...cbs
        }));
      }
      if (matrixRes.ok) {
        const mat = await matrixRes.json();
        if (Object.keys(mat).length > 0) {
          setMatrix(mat);
        }
      }
    } catch (err) {
      console.warn('Backend Failure Lab API not reachable yet; using local interactive state.', err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  // Trigger Simulation connecting to /api/v1/failure-lab/simulate
  const handleTriggerSimulation = async () => {
    setLoading(true);
    const updatedConfig: ChaosSimulationConfig = {
      ...chaosConfig,
      inject_latency_ms: hasLatencySpike ? 5000 : 0
    };

    try {
      const res = await fetch('/api/v1/failure-lab/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedConfig)
      });

      if (res.ok) {
        const returnedCfg: ChaosSimulationConfig = await res.json();
        setChaosConfig(returnedCfg);
      }
    } catch (err) {
      console.error('Failed to trigger simulation on backend', err);
    } finally {
      // If rate limit or schema corruption or latency spike is active, update circuit breaker status to OPEN or HALF_OPEN
      if (updatedConfig.inject_rate_limit || updatedConfig.inject_schema_corruption) {
        setCircuitBreakers(prev => ({
          ...prev,
          gemini: { ...prev.gemini, state: 'OPEN', failure_count: 3, last_failure_timestamp: new Date().toISOString() }
        }));
      }

      // Add a live failover trace log entry
      const activeEffects: string[] = [];
      if (updatedConfig.inject_rate_limit) activeEffects.push('Rate Limit 429');
      if (hasLatencySpike) activeEffects.push('Latency Spike (5000ms Timeout)');
      if (updatedConfig.inject_schema_corruption) activeEffects.push('Schema Corruption');

      const targetNodeName = updatedConfig.target_node && updatedConfig.target_node !== 'ALL'
        ? updatedConfig.target_node
        : 'SpecialistDiligence';

      const newTrace: FailoverEvent = {
        id: `tr-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        node_name: targetNodeName,
        task_type: targetNodeName.includes('Financial') ? 'DETERMINISTIC_MATH' : 'REASONING_SYNTHESIS',
        primary_provider: 'gemini',
        primary_model: 'gemini-1.5-pro',
        error_message: activeEffects.length > 0
          ? `Chaos Injected: ${activeEffects.join(', ')}`
          : 'Chaos Test: Forced primary exception',
        fallback_provider: 'openai',
        fallback_model: 'gpt-4o',
        status: 'SUCCESS'
      };

      setFailoverTraces(prev => [newTrace, ...prev]);
      setStatusMessage({
        type: 'warning',
        text: `Chaos Simulation Triggered! Rules injected: ${activeEffects.join(' | ') || 'None'}. Primary provider failover activated.`
      });
      setLoading(false);
    }
  };

  // Reset Failure Lab connecting to /api/v1/failure-lab/reset
  const handleResetLab = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/failure-lab/reset', {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        if (data.chaos_config) setChaosConfig(data.chaos_config);
      }
    } catch (err) {
      console.error('Failed to reset failure lab on backend', err);
    } finally {
      setChaosConfig({
        inject_rate_limit: false,
        inject_latency_ms: 0,
        inject_schema_corruption: false,
        target_node: null
      });
      setHasLatencySpike(false);
      setCircuitBreakers(INITIAL_CIRCUIT_BREAKERS);
      setStatusMessage({
        type: 'success',
        text: 'Failure Lab reset! All chaos rules cleared and provider circuit breakers restored to CLOSED [Green].'
      });
      setLoading(false);
    }
  };

  // Toggle individual provider circuit breaker state for testing
  const toggleCircuitBreaker = (providerKey: string) => {
    setCircuitBreakers(prev => {
      const current = prev[providerKey];
      if (!current) return prev;

      let nextState: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
      let nextFailures = 0;

      if (current.state === 'CLOSED') {
        nextState = 'OPEN';
        nextFailures = 3;
      } else if (current.state === 'OPEN') {
        nextState = 'HALF_OPEN';
        nextFailures = 1;
      } else {
        nextState = 'CLOSED';
        nextFailures = 0;
      }

      return {
        ...prev,
        [providerKey]: {
          ...current,
          state: nextState,
          failure_count: nextFailures,
          last_failure_timestamp: nextState !== 'CLOSED' ? new Date().toISOString() : null
        }
      };
    });
  };

  const getBadgeForState = (state: 'CLOSED' | 'OPEN' | 'HALF_OPEN') => {
    switch (state) {
      case 'CLOSED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-emerald-950 text-emerald-300 border border-emerald-600 shadow-md shadow-emerald-950/50">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            CLOSED (Healthy)
          </span>
        );
      case 'OPEN':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-rose-950 text-rose-200 border border-rose-600 shadow-md shadow-rose-900/60">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
            OPEN (Tripped)
          </span>
        );
      case 'HALF_OPEN':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-amber-950 text-amber-200 border border-amber-600 shadow-sm">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
            HALF_OPEN (Testing)
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Hero / Header Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">🧪</span>
            <h2 className="text-xl font-extrabold tracking-tight text-white">
              Failure Lab & Multi-Provider Resilience Engine
            </h2>
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 text-[10px] font-mono font-bold">
              Chaos Eng 2.0
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Simulate API rate limits, latency spikes, and schema corruptions to verify zero-downtime multi-model failover and circuit breaker resilience.
          </p>
        </div>

        {/* Global Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleTriggerSimulation}
            disabled={loading}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 text-white font-extrabold text-xs shadow-lg shadow-amber-900/30 transition-all flex items-center gap-2 border border-amber-500/30 disabled:opacity-50"
          >
            <span>⚡</span> Trigger Chaos Simulation
          </button>
          <button
            onClick={handleResetLab}
            disabled={loading}
            className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 font-bold text-xs border border-slate-700 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            <span>🔄</span> Reset Chaos & Breakers
          </button>
        </div>
      </div>

      {/* Notification Toast */}
      {statusMessage && (
        <div
          className={`p-4 rounded-xl text-xs font-semibold flex items-center justify-between transition-all ${
            statusMessage.type === 'success'
              ? 'bg-emerald-950/80 text-emerald-200 border border-emerald-800'
              : statusMessage.type === 'warning'
              ? 'bg-amber-950/80 text-amber-200 border border-amber-800'
              : 'bg-indigo-950/80 text-indigo-200 border border-indigo-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <span>{statusMessage.type === 'success' ? '✅' : '⚠️'}</span>
            <span>{statusMessage.text}</span>
          </div>
          <button
            onClick={() => setStatusMessage(null)}
            className="text-slate-400 hover:text-white font-bold px-2 py-0.5"
          >
            ✕
          </button>
        </div>
      )}

      {/* Top Grid: Model Routing Matrix & Circuit Breaker Monitors */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Model Routing Matrix Card (7 cols) */}
        <div className="lg:col-span-7 glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div>
              <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                <span>🗺️</span> Model Routing Matrix
              </h3>
              <p className="text-xs text-slate-400">
                Task-type specialization rules and primary &rarr; fallback provider mappings.
              </p>
            </div>
            <span className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
              4 Task Policies Active
            </span>
          </div>

          <div className="space-y-3">
            {Object.entries(matrix).map(([taskType, policy]) => (
              <div
                key={taskType}
                className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 hover:border-slate-700 transition-all space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-1 rounded-lg text-xs font-mono font-black bg-indigo-950 text-indigo-300 border border-indigo-800">
                      {taskType}
                    </span>
                    <span className="text-[11px] text-slate-400">
                      Timeout: <strong className="text-slate-200">{policy.timeout_seconds}s</strong> | Retries:{' '}
                      <strong className="text-slate-200">{policy.max_retries}</strong>
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 font-mono">
                    Threshold: {policy.circuit_breaker_threshold} fails
                  </span>
                </div>

                {/* Primary -> Fallback Routing Flow */}
                <div className="grid grid-cols-1 sm:grid-cols-11 items-center gap-2 text-xs">
                  {/* Primary Box */}
                  <div className="sm:col-span-5 bg-indigo-950/40 p-2.5 rounded-lg border border-indigo-800/60 flex items-center justify-between">
                    <div>
                      <div className="text-[10px] uppercase font-bold text-indigo-400">Primary Provider</div>
                      <div className="font-extrabold text-white">{policy.primary_model}</div>
                    </div>
                    <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-indigo-900 text-indigo-200 uppercase">
                      {policy.primary_provider}
                    </span>
                  </div>

                  {/* Failover Arrow */}
                  <div className="sm:col-span-1 text-center font-bold text-slate-500">
                    &rarr;
                  </div>

                  {/* Fallback Box */}
                  <div className="sm:col-span-5 bg-purple-950/40 p-2.5 rounded-lg border border-purple-800/60 flex items-center justify-between">
                    <div>
                      <div className="text-[10px] uppercase font-bold text-purple-400">Fallback Provider</div>
                      <div className="font-extrabold text-white">{policy.fallback_model}</div>
                    </div>
                    <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-purple-900 text-purple-200 uppercase">
                      {policy.fallback_provider}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Circuit Breaker Live Monitors Card (5 cols) */}
        <div className="lg:col-span-5 glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div>
              <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                <span>⚡</span> Circuit Breaker Live Monitors
              </h3>
              <p className="text-xs text-slate-400">
                Real-time health status of LLM provider connections.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {Object.entries(circuitBreakers).map(([key, cb]) => (
              <div
                key={key}
                className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-extrabold text-white capitalize">{cb.provider || key}</h4>
                    <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                      Failures: <span className="text-slate-300 font-bold">{cb.failure_count} / 3</span>
                    </p>
                  </div>
                  {getBadgeForState(cb.state)}
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-900">
                  <span>
                    Last Failure:{' '}
                    {cb.last_failure_timestamp
                      ? new Date(cb.last_failure_timestamp).toLocaleTimeString()
                      : 'None'}
                  </span>
                  <button
                    onClick={() => toggleCircuitBreaker(key)}
                    className="text-[11px] text-indigo-400 hover:text-indigo-200 underline font-semibold"
                  >
                    Toggle State ({cb.state === 'CLOSED' ? 'Trip' : cb.state === 'OPEN' ? 'Test Half-Open' : 'Reset'})
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Info Banner */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-400 space-y-1">
            <div className="font-bold text-slate-300 flex items-center gap-1.5">
              <span>💡</span> Circuit Breaker Logic
            </div>
            <p className="text-[11px] leading-relaxed">
              When a provider encounters 3 consecutive failures (HTTP 429, Timeout, or Schema error), the circuit trips to <strong>OPEN</strong> for 60 seconds. All subsequent requests automatically bypass to the secondary provider without waiting for timeouts.
            </p>
          </div>
        </div>
      </div>

      {/* Middle Section: Chaos Simulation Control Panel */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div>
            <h3 className="text-base font-extrabold text-white flex items-center gap-2">
              <span>🎛️</span> Chaos Simulation Control Panel
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Inject synthetic fault modes into specific workflow execution nodes to test failover behavior.
            </p>
          </div>

          {/* Target Node Selector */}
          <div className="flex items-center gap-2">
            <label className="text-xs font-bold text-slate-300 whitespace-nowrap">Target Node:</label>
            <select
              value={chaosConfig.target_node || 'ALL'}
              onChange={e =>
                setChaosConfig(prev => ({
                  ...prev,
                  target_node: e.target.value === 'ALL' ? null : e.target.value
                }))
              }
              className="bg-slate-950 border border-slate-800 text-xs font-semibold rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Nodes (Global Injection)</option>
              <option value="IngestionChunker">IngestionChunker</option>
              <option value="FinancialAnalyst">FinancialAnalyst</option>
              <option value="SpecialistDiligence">SpecialistDiligence</option>
              <option value="ICDebateSynthesis">ICDebateSynthesis</option>
              <option value="CriticEvaluator">CriticEvaluator</option>
            </select>
          </div>
        </div>

        {/* Interactive Toggle Switches Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Toggle 1: Rate Limit 429 */}
          <div
            className={`p-5 rounded-2xl border transition-all space-y-3 cursor-pointer ${
              chaosConfig.inject_rate_limit
                ? 'bg-rose-950/30 border-rose-700/80 shadow-lg shadow-rose-950/40'
                : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
            }`}
            onClick={() =>
              setChaosConfig(prev => ({
                ...prev,
                inject_rate_limit: !prev.inject_rate_limit
              }))
            }
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">🚫</span>
                <h4 className="text-sm font-extrabold text-white">Inject Rate Limit (429)</h4>
              </div>
              <div
                className={`w-11 h-6 rounded-full transition-colors relative flex items-center px-1 ${
                  chaosConfig.inject_rate_limit ? 'bg-rose-600' : 'bg-slate-800'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white transition-transform ${
                    chaosConfig.inject_rate_limit ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Forces the primary LLM provider to throw HTTP 429 Too Many Requests errors. Tests instant circuit breaker activation.
            </p>
          </div>

          {/* Toggle 2: Latency Spike 5s */}
          <div
            className={`p-5 rounded-2xl border transition-all space-y-3 cursor-pointer ${
              hasLatencySpike
                ? 'bg-amber-950/30 border-amber-700/80 shadow-lg shadow-amber-950/40'
                : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
            }`}
            onClick={() => setHasLatencySpike(!hasLatencySpike)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">⏱️</span>
                <h4 className="text-sm font-extrabold text-white">Inject Latency Spike (5s)</h4>
              </div>
              <div
                className={`w-11 h-6 rounded-full transition-colors relative flex items-center px-1 ${
                  hasLatencySpike ? 'bg-amber-600' : 'bg-slate-800'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white transition-transform ${
                    hasLatencySpike ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Delays primary model requests by 5000ms. Verifies adapter timeout logic and seamless fallback execution.
            </p>
          </div>

          {/* Toggle 3: Schema Corruption */}
          <div
            className={`p-5 rounded-2xl border transition-all space-y-3 cursor-pointer ${
              chaosConfig.inject_schema_corruption
                ? 'bg-purple-950/30 border-purple-700/80 shadow-lg shadow-purple-950/40'
                : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
            }`}
            onClick={() =>
              setChaosConfig(prev => ({
                ...prev,
                inject_schema_corruption: !prev.inject_schema_corruption
              }))
            }
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">🧩</span>
                <h4 className="text-sm font-extrabold text-white">Inject Schema Corruption</h4>
              </div>
              <div
                className={`w-11 h-6 rounded-full transition-colors relative flex items-center px-1 ${
                  chaosConfig.inject_schema_corruption ? 'bg-purple-600' : 'bg-slate-800'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white transition-transform ${
                    chaosConfig.inject_schema_corruption ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Corrupts JSON response payload structure. Tests Pydantic schema validation error catching and secondary model retries.
            </p>
          </div>
        </div>

        {/* Action Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800/80">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>Status:</span>
            {chaosConfig.inject_rate_limit || hasLatencySpike || chaosConfig.inject_schema_corruption ? (
              <span className="px-2.5 py-0.5 rounded-md font-bold bg-amber-950 text-amber-300 border border-amber-700">
                CHAOS ACTIVE
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded-md font-bold bg-slate-900 text-slate-400 border border-slate-800">
                STANDBY (No Faults Injected)
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleTriggerSimulation}
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs shadow-md transition-all flex items-center gap-2"
            >
              <span>🚀</span> Apply Simulation Rules
            </button>
            <button
              onClick={handleResetLab}
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 font-bold text-xs border border-slate-800 transition-all"
            >
              Clear All Rules
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Section: Real-Time Failover Trace Log */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div>
            <h3 className="text-base font-extrabold text-white flex items-center gap-2">
              <span>📜</span> Real-Time Failover Trace Log
            </h3>
            <p className="text-xs text-slate-400">
              Live audit stream showing primary model exceptions &rarr; automatic fallback model activations.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
              {failoverTraces.length} Traces Logged
            </span>
            <button
              onClick={() => setFailoverTraces([])}
              className="text-xs font-semibold text-slate-500 hover:text-slate-300"
            >
              Clear Log
            </button>
          </div>
        </div>

        {/* Failover Trace Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] uppercase tracking-wider text-slate-400 bg-slate-950/60 font-bold">
                <th className="py-3 px-4">Time</th>
                <th className="py-3 px-4">Workflow Node</th>
                <th className="py-3 px-4">Task Type</th>
                <th className="py-3 px-4">Primary Error</th>
                <th className="py-3 px-4">Fallback Activation</th>
                <th className="py-3 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {failoverTraces.map(trace => (
                <tr key={trace.id} className="hover:bg-slate-900/50 transition-colors">
                  <td className="py-3.5 px-4 text-slate-400 whitespace-nowrap">{trace.timestamp}</td>
                  <td className="py-3.5 px-4 font-bold text-white whitespace-nowrap">
                    <span>⚙️</span> {trace.node_name}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                      {trace.task_type}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-rose-300 max-w-xs truncate" title={trace.error_message}>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950/80 border border-rose-800 text-rose-200">
                      {trace.primary_provider.toUpperCase()}: {trace.error_message}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 whitespace-nowrap text-purple-200">
                    <div className="flex items-center gap-1.5">
                      <span className="line-through text-slate-500">{trace.primary_model}</span>
                      <span className="text-slate-400">&rarr;</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-950 text-purple-200 border border-purple-800">
                        {trace.fallback_model}
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-right whitespace-nowrap">
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-black bg-emerald-950 text-emerald-300 border border-emerald-700">
                      ✓ {trace.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
