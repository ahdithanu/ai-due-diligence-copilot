import React, { useState } from 'react';
import { DiligenceState, DeploymentConfig, CheckpointRecord } from '../types';

interface OperatorControlCenterProps {
  state: DiligenceState;
  deployments: DeploymentConfig[];
  selectedDeploymentId?: string;
  onSelectDeployment: (deploymentId: string) => void;
  onPause: () => Promise<void>;
  onResume: () => Promise<void>;
  onRetry: (failedNode?: string) => Promise<void>;
  onResolveConflict: (authoritativeEvidenceId: string, conflictId?: string, notes?: string) => Promise<void>;
  checkpoints?: CheckpointRecord[];
}

export const OperatorControlCenter: React.FC<OperatorControlCenterProps> = ({
  state,
  deployments,
  selectedDeploymentId,
  onSelectDeployment,
  onPause,
  onResume,
  onRetry,
  onResolveConflict,
  checkpoints = []
}) => {
  const [showConflictModal, setShowConflictModal] = useState(false);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string>('');
  const [selectedConflictId, setSelectedConflictId] = useState<string>('');
  const [resolutionNotes, setResolutionNotes] = useState<string>('');
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const activeDeployment = deployments.find(
    d => d.deployment_id === (selectedDeploymentId || state.deployment_id || state.deployment_config?.deployment_id)
  ) || state.deployment_config || deployments[0];

  const currentState = state.execution_state || (
    state.status === 'FAILED' ? 'FAILED' :
    state.human_review_required || state.status === 'HUMAN_REVIEW' ? 'WAITING_FOR_HUMAN' :
    state.status === 'COMPLETED' || state.status === 'MEMO_GENERATED' ? 'COMPLETED' :
    'RUNNING'
  );

  const effectiveCheckpoints = (checkpoints && checkpoints.length > 0)
    ? checkpoints
    : (state.checkpoint_history || []);

  const handlePauseClick = async () => {
    setActionInProgress('pause');
    try {
      await onPause();
    } finally {
      setActionInProgress(null);
    }
  };

  const handleResumeClick = async () => {
    setActionInProgress('resume');
    try {
      await onResume();
    } finally {
      setActionInProgress(null);
    }
  };

  const handleRetryClick = async () => {
    setActionInProgress('retry');
    try {
      const failedNode = state.failure_details?.failed_node;
      await onRetry(failedNode);
    } finally {
      setActionInProgress(null);
    }
  };

  const handleResolveConflictSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvidenceId && state.evidence_records.length > 0) {
      alert('Please select an authoritative evidence record');
      return;
    }
    setActionInProgress('resolve');
    try {
      await onResolveConflict(
        selectedEvidenceId || (state.evidence_records[0]?.id || 'evidence-authoritative-1'),
        selectedConflictId || undefined,
        resolutionNotes
      );
      setShowConflictModal(false);
      setResolutionNotes('');
    } finally {
      setActionInProgress(null);
    }
  };

  const getExecutionStateBadge = (execState: string) => {
    switch (execState) {
      case 'RUNNING':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-950/80 text-indigo-300 border border-indigo-500/50 shadow-sm shadow-indigo-500/30">
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>
            <span>RUNNING</span>
          </span>
        );
      case 'PAUSED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-950/80 text-amber-300 border border-amber-500/50">
            <span>⏸️ PAUSED</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-950/80 text-rose-300 border border-rose-500/50 animate-pulse">
            <span>🔴 FAILED</span>
          </span>
        );
      case 'WAITING_FOR_HUMAN':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-purple-950/80 text-purple-300 border border-purple-500/50">
            <span>👤 WAITING FOR HUMAN</span>
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-500/50">
            <span>✓ COMPLETED</span>
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700">
            <span>🚫 CANCELLED</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-300 border border-slate-700">
            <span>{execState}</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Dashboard Top Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-indigo-500/30 space-y-4 bg-gradient-to-r from-slate-950 via-slate-900 to-indigo-950/40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
                <span>🛡️ Operator Control Center</span>
              </h2>
              {/* Live Execution State Badge */}
              {getExecutionStateBadge(currentState)}
            </div>
            <p className="text-xs text-slate-400">
              Autonomous Diligence Monitoring, Checkpoint Supervision & Human-in-the-Loop Recovery Controls
            </p>
          </div>

          {/* Deployment Selector & Customer Deployment Badge */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex flex-col items-end">
              <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Customer Deployment Profile</label>
              <select
                value={activeDeployment?.deployment_id || ''}
                onChange={e => onSelectDeployment(e.target.value)}
                className="mt-1 px-3 py-1.5 rounded-xl bg-slate-900 border border-indigo-500/40 text-slate-100 font-semibold text-xs focus:outline-none focus:border-indigo-400"
              >
                {deployments.map(dep => (
                  <option key={dep.deployment_id} value={dep.deployment_id}>
                    {dep.investment_strategy === 'growth_equity_saas' ? 'Growth Equity SaaS' : 'Traditional Buyout'} - {dep.customer_name} ({dep.deployment_name})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Active Deployment Details Badge Strip */}
        {activeDeployment && (
          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-sans">Active Strategy:</span>
              <span className="px-2.5 py-0.5 rounded-md bg-indigo-950 text-indigo-300 border border-indigo-800 font-bold uppercase">
                {activeDeployment.investment_strategy.replace('_', ' ')}
              </span>
              <span className="text-slate-300 font-semibold font-sans ml-1">
                {activeDeployment.customer_name} &bull; {activeDeployment.deployment_name}
              </span>
            </div>

            <div className="flex items-center gap-4 text-[11px] text-slate-400">
              {activeDeployment.financial_thresholds?.min_gross_margin !== undefined && (
                <span>Min GM: <strong className="text-emerald-400">{(activeDeployment.financial_thresholds.min_gross_margin * 100).toFixed(0)}%</strong></span>
              )}
              {activeDeployment.financial_thresholds?.min_nrr_pct !== undefined && (
                <span>Min NRR: <strong className="text-indigo-400">{activeDeployment.financial_thresholds.min_nrr_pct}%</strong></span>
              )}
              {activeDeployment.evaluation_thresholds?.min_quality_score !== undefined && (
                <span>Qual Threshold: <strong className="text-cyan-400">{(activeDeployment.evaluation_thresholds.min_quality_score * 100).toFixed(0)}%</strong></span>
              )}
            </div>
          </div>
        )}

        {/* Operator Action Controls Bar */}
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-800">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider mr-2">Operator Actions:</span>
          
          <button
            onClick={handlePauseClick}
            disabled={currentState !== 'RUNNING' || actionInProgress !== null}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              currentState === 'RUNNING'
                ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-md shadow-amber-600/20'
                : 'bg-slate-800 text-slate-500 opacity-60 cursor-not-allowed'
            }`}
          >
            <span>⏸️</span> {actionInProgress === 'pause' ? 'Pausing...' : 'Pause Graph'}
          </button>

          <button
            onClick={handleResumeClick}
            disabled={(currentState !== 'PAUSED' && currentState !== 'WAITING_FOR_HUMAN') || actionInProgress !== null}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              currentState === 'PAUSED' || currentState === 'WAITING_FOR_HUMAN'
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/20'
                : 'bg-slate-800 text-slate-500 opacity-60 cursor-not-allowed'
            }`}
          >
            <span>▶</span> {actionInProgress === 'resume' ? 'Resuming...' : 'Resume Graph'}
          </button>

          <button
            onClick={handleRetryClick}
            disabled={(currentState !== 'FAILED' && currentState !== 'WAITING_FOR_HUMAN') || actionInProgress !== null}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              currentState === 'FAILED' || currentState === 'WAITING_FOR_HUMAN'
                ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20'
                : 'bg-slate-800 text-slate-500 opacity-60 cursor-not-allowed'
            }`}
          >
            <span>🔄</span> {actionInProgress === 'retry' ? 'Retrying...' : 'Retry Failed Node'}
          </button>

          <button
            onClick={() => setShowConflictModal(true)}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-600/90 hover:bg-rose-500 text-white shadow-md shadow-rose-600/20 transition-all flex items-center gap-1.5"
          >
            <span>⚖️</span> Resolve Evidence Conflict
          </button>
        </div>
      </div>

      {/* Failure / Escalation Card */}
      {(currentState === 'FAILED' || currentState === 'WAITING_FOR_HUMAN' || state.failure_details || state.human_review_required) && (
        <div className="glass-panel p-6 rounded-2xl border-2 border-rose-500/70 bg-rose-950/30 space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🚨</span>
              <div>
                <h3 className="text-lg font-extrabold text-rose-200">
                  {currentState === 'FAILED' ? 'Execution Failure Recorded' : 'Human Escalation Gate Triggered'}
                </h3>
                <p className="text-xs text-rose-300/80">
                  Operator intervention required to resolve conflict or retry failed node checkpoint.
                </p>
              </div>
            </div>
            {getExecutionStateBadge(currentState)}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-950/80 p-4 rounded-xl border border-rose-900/60 space-y-2 text-xs font-mono">
              <div>
                <span className="text-rose-400 font-bold block uppercase tracking-wider text-[10px]">Failed / Escalated Node:</span>
                <span className="text-slate-200 font-bold">
                  {state.failure_details?.failed_node || (state.human_review_required ? 'HumanReviewGateNode' : 'UnknownNode')}
                </span>
              </div>
              <div>
                <span className="text-rose-400 font-bold block uppercase tracking-wider text-[10px]">Error / Exception Type:</span>
                <span className="text-amber-300">
                  {state.failure_details?.error_type || 'HumanReviewRequiredException'}
                </span>
              </div>
              <div>
                <span className="text-rose-400 font-bold block uppercase tracking-wider text-[10px]">Error Message:</span>
                <p className="text-slate-300 whitespace-pre-wrap">
                  {state.failure_details?.error_message || (state.human_review_reasons && state.human_review_reasons.join('; ')) || 'Contradiction or low confidence score triggered review.'}
                </p>
              </div>
            </div>

            <div className="bg-slate-950/80 p-4 rounded-xl border border-rose-900/60 space-y-2 text-xs">
              <div>
                <span className="text-rose-400 font-bold block uppercase tracking-wider text-[10px]">Suggested Recovery Action:</span>
                <p className="text-emerald-300 font-semibold mt-0.5">
                  {state.failure_details?.suggested_recovery_action || 'Review conflicting evidence records, select authoritative source or override parameters.'}
                </p>
              </div>

              {state.contradictions && state.contradictions.length > 0 && (
                <div className="pt-2 border-t border-rose-900/40">
                  <span className="text-rose-400 font-bold block uppercase tracking-wider text-[10px] mb-1">Conflicting Evidence Details:</span>
                  <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                    {state.contradictions.map(c => (
                      <div key={c.id} className="bg-rose-950/50 p-2 rounded border border-rose-800/40 font-mono text-[11px]">
                        <span className="text-rose-200 font-semibold">{c.description}</span>
                        <span className="text-[10px] text-rose-400 block">Status: {c.status} &bull; Materiality: {c.materiality}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={() => setShowConflictModal(true)}
              className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow"
            >
              Resolve Conflict Modal &rarr;
            </button>
            <button
              onClick={handleRetryClick}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow"
            >
              Retry Node Execution &rarr;
            </button>
          </div>
        </div>
      )}

      {/* Checkpoint Timeline */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>📍 Persisted Node Checkpoints Timeline</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-900 text-indigo-300 border border-slate-800 font-mono">
                {effectiveCheckpoints.length} Checkpoints
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Auditable execution version history with state snapshots & routing decisions
            </p>
          </div>
        </div>

        {effectiveCheckpoints.length === 0 ? (
          <div className="bg-slate-950/60 p-8 text-center text-slate-500 rounded-xl border border-dashed border-slate-800 text-xs">
            No graph checkpoints recorded yet. Run graph execution to record node checkpoints.
          </div>
        ) : (
          <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
            {effectiveCheckpoints.map((cp, idx) => (
              <div key={cp.checkpoint_id || idx} className="relative group">
                {/* Timeline Dot */}
                <div className={`absolute -left-6 top-3 w-3 h-3 rounded-full border-2 ${
                  cp.status === 'COMPLETED' ? 'bg-emerald-500 border-slate-900' :
                  cp.status === 'FAILED' ? 'bg-rose-500 border-slate-900' :
                  'bg-indigo-500 border-slate-900'
                }`}></div>

                <div className="glass-card p-4 rounded-xl border border-slate-800/80 hover:border-indigo-500/40 transition-all">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className="font-bold text-white text-sm">{cp.node_id}</span>
                      <span className="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 text-[10px]">
                        State v{cp.graph_state_version}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 text-[10px]">
                        Iter #{cp.iteration_count}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      {new Date(cp.timestamp).toLocaleString()}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono text-slate-300 bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
                    <div>
                      <span className="text-slate-500 block text-[10px] uppercase">Routing Decision:</span>
                      <span className="text-cyan-300 font-semibold">{cp.routing_decision || 'next_node'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px] uppercase">Execution Status:</span>
                      <span className={cp.status === 'FAILED' ? 'text-rose-400 font-bold' : 'text-emerald-400 font-semibold'}>
                        {cp.status}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Resolve Conflict Modal */}
      {showConflictModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
          <div className="glass-panel w-full max-w-xl p-6 rounded-2xl border border-rose-500/40 shadow-2xl space-y-5">
            <div className="flex justify-between items-center pb-3 border-b border-slate-800">
              <h3 className="text-lg font-extrabold text-white flex items-center gap-2">
                <span>⚖️ Resolve Evidence Conflict</span>
              </h3>
              <button onClick={() => setShowConflictModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <p className="text-xs text-slate-300">
              Select the authoritative evidence source to override conflicting claims and proceed with diligence synthesis.
            </p>

            <form onSubmit={handleResolveConflictSubmit} className="space-y-4">
              {/* Conflict selection if multiple */}
              {state.contradictions && state.contradictions.length > 0 && (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Target Conflict / Contradiction Record</label>
                  <select
                    value={selectedConflictId}
                    onChange={e => setSelectedConflictId(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-xs focus:outline-none focus:border-rose-500"
                  >
                    <option value="">All Open Conflicts</option>
                    {state.contradictions.map(c => (
                      <option key={c.id} value={c.id}>
                        {c.description} ({c.materiality})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Authoritative Evidence Selection */}
              <div>
                <label className="block text-xs font-semibold text-rose-300 mb-1">Authoritative Evidence Source Selection</label>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {state.evidence_records.length === 0 ? (
                    <div className="text-xs text-slate-400 p-3 bg-slate-950 rounded-xl border border-slate-800">
                      No extracted evidence records found. Default authoritative source will be created.
                    </div>
                  ) : (
                    state.evidence_records.map(ev => (
                      <label
                        key={ev.id}
                        className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                          selectedEvidenceId === ev.id
                            ? 'bg-rose-950/60 border-rose-500 text-slate-100'
                            : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700'
                        }`}
                      >
                        <input
                          type="radio"
                          name="authoritativeEvidence"
                          value={ev.id}
                          checked={selectedEvidenceId === ev.id}
                          onChange={() => setSelectedEvidenceId(ev.id)}
                          className="mt-1 accent-rose-500"
                        />
                        <div className="text-xs space-y-0.5">
                          <span className="font-bold text-white block">{ev.section_title || 'Evidence Record'} (Doc: {ev.document_id})</span>
                          <p className="text-slate-300 line-clamp-2">{ev.content}</p>
                          <span className="text-[10px] text-emerald-400 font-mono block">Confidence: {(ev.confidence * 100).toFixed(0)}%</span>
                        </div>
                      </label>
                    ))
                  )}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Operator Resolution Rationale / Notes</label>
                <textarea
                  rows={2}
                  placeholder="Explain why this evidence source is authoritative (e.g. audited 10-K report overrides draft deck)..."
                  value={resolutionNotes}
                  onChange={e => setResolutionNotes(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-xs focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowConflictModal(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionInProgress !== null}
                  className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-md"
                >
                  {actionInProgress === 'resolve' ? 'Resolving...' : 'Confirm & Resolve Conflict'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
