import React, { useState } from 'react';
import { DiligenceState, ExecutionLogEntry, DeploymentConfig, CheckpointRecord } from '../types';
import { OperatorControlCenter } from './OperatorControlCenter';

interface GraphVisualizerProps {
  state: DiligenceState;
  logs: ExecutionLogEntry[];
  deployments: DeploymentConfig[];
  selectedDeploymentId?: string;
  onSelectDeployment: (id: string) => void;
  onStartDiligence: (domain?: string) => Promise<void>;
  onResumeDiligence: (action: string, feedback?: string, newEvidence?: any[]) => Promise<void>;
  onRerunNode: (fromNode: string) => Promise<void>;
  onPauseDiligence: () => Promise<void>;
  onRetryNode: (failedNode?: string) => Promise<void>;
  onResolveConflict: (authoritativeEvidenceId: string, conflictId?: string, notes?: string) => Promise<void>;
  checkpoints?: CheckpointRecord[];
  running: boolean;
}

interface GraphNodeDef {
  id: string;
  label: string;
  category: 'ingestion' | 'engine' | 'specialist' | 'critic' | 'ic' | 'output' | 'gate';
  description: string;
}

const GRAPH_NODES: GraphNodeDef[] = [
  { id: 'Ingestion', label: 'Document Ingestion', category: 'ingestion', description: 'Raw document upload & storage' },
  { id: 'Parser', label: 'Document Parser', category: 'ingestion', description: 'Chunking & structural extraction' },
  { id: 'EvidenceExtractor', label: 'Evidence Extractor', category: 'ingestion', description: 'Claim extraction & confidence scoring' },
  { id: 'FinancialEngine', label: 'Financial Engine', category: 'engine', description: 'Deterministic math & formula validation' },
  { id: 'FinancialAnalystGenerator', label: 'Financial Specialist', category: 'specialist', description: 'Financial analysis generator' },
  { id: 'FinancialCriticEvaluator', label: 'Financial Critic', category: 'critic', description: 'Evidence coverage & citation auditor' },
  { id: 'CrossExaminerNode', label: 'Cross Examiner', category: 'critic', description: 'Contradiction detection across evidence' },
  { id: 'GapDetectorNode', label: 'Gap Detector', category: 'critic', description: 'Prioritized question generation' },
  { id: 'BullNode', label: 'Bull Specialist', category: 'ic', description: 'Evidence-grounded upside case' },
  { id: 'BearNode', label: 'Bear Specialist', category: 'ic', description: 'Risk-grounded downside case' },
  { id: 'SkepticNode', label: 'Skeptic Reviewer', category: 'ic', description: 'Attacks assumptions & missing proof' },
  { id: 'ICSynthesizer', label: 'IC Synthesizer', category: 'ic', description: 'Thesis, recommendation & confidence score' },
  { id: 'HumanReviewGateNode', label: 'Human Review Gate', category: 'gate', description: 'Interrupts low confidence & contradictions' },
  { id: 'MemoGeneratorNode', label: 'Institutional Memo', category: 'output', description: 'Markdown memo rendering with popover citations' },
];

export const GraphVisualizer: React.FC<GraphVisualizerProps> = ({
  state,
  logs,
  deployments,
  selectedDeploymentId,
  onSelectDeployment,
  onStartDiligence,
  onResumeDiligence,
  onRerunNode,
  onPauseDiligence,
  onRetryNode,
  onResolveConflict,
  checkpoints = [],
  running
}) => {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [actionType, setActionType] = useState<'APPROVE' | 'REJECT' | 'ADD_EVIDENCE'>('APPROVE');
  const [humanFeedback, setHumanFeedback] = useState('');
  const [evidenceText, setEvidenceText] = useState('');
  const [submittingAction, setSubmittingAction] = useState(false);
  const [activeStreamNode, setActiveStreamNode] = useState<string | null>(null);
  const [streamCompletedNodes, setStreamCompletedNodes] = useState<Set<string>>(new Set());
  const [isStreaming, setIsStreaming] = useState(false);

  // Map executed nodes from state & logs
  const executedNodeNames = new Set(logs.map(l => l.node_name));
  const latestLog = logs.length > 0 ? logs[logs.length - 1] : null;

  const handleStartSSEStream = () => {
    if (!state.investment_id || isStreaming || running) return;
    setIsStreaming(true);
    setActiveStreamNode(null);
    setStreamCompletedNodes(new Set());

    const eventSource = new EventSource(`/api/v1/investments/${state.investment_id}/diligence/stream`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === 'node_start') {
          setActiveStreamNode(data.node);
        } else if (data.event === 'node_complete') {
          setActiveStreamNode(null);
          setStreamCompletedNodes((prev) => new Set(prev).add(data.node));
        } else if (data.event === 'human_review' || data.event === 'diligence_complete') {
          setActiveStreamNode(null);
          setIsStreaming(false);
          eventSource.close();
          onStartDiligence('Financial');
        }
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE connection error:', err);
      setActiveStreamNode(null);
      setIsStreaming(false);
      eventSource.close();
    };
  };

  const handleResumeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingAction(true);
    try {
      const newEv = actionType === 'ADD_EVIDENCE' && evidenceText ? [{ content: evidenceText }] : undefined;
      await onResumeDiligence(actionType, humanFeedback, newEv);
      setHumanFeedback('');
      setEvidenceText('');
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingAction(false);
    }
  };

  const getNodeStatus = (nodeId: string) => {
    if (state.human_review_required && nodeId === 'HumanReviewGateNode') {
      return 'review';
    }
    if (activeStreamNode === nodeId || (latestLog && latestLog.node_name === nodeId && latestLog.status === 'RUNNING')) {
      return 'running';
    }
    if (executedNodeNames.has(nodeId) || streamCompletedNodes.has(nodeId)) {
      return 'completed';
    }
    return 'pending';
  };

  const getCategoryColor = (category: string, status: string) => {
    if (status === 'review') return 'bg-rose-950/80 border-rose-500 text-rose-200 shadow-rose-900/50';
    if (status === 'running') return 'node-running bg-indigo-950/80 border-indigo-400 text-indigo-100';
    if (status === 'completed') return 'bg-slate-900/90 border-emerald-500/60 text-slate-100';
    return 'bg-slate-950/40 border-slate-800 text-slate-500';
  };

  return (
    <div className="space-y-6">
      {/* Operator Control Center */}
      <OperatorControlCenter
        state={state}
        deployments={deployments}
        selectedDeploymentId={selectedDeploymentId}
        onSelectDeployment={onSelectDeployment}
        onPause={onPauseDiligence}
        onResume={() => onResumeDiligence('APPROVE')}
        onRetry={onRetryNode}
        onResolveConflict={onResolveConflict}
        checkpoints={checkpoints}
      />

      {/* Top Controls */}
      <div className="glass-panel p-5 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 border border-indigo-500/20">
        <div>
          <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
            <span>🕸️ Graph Execution Engine</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono">
              DAG Visualizer
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Generate-Critique-Judge-Revise State Machine & Dynamic Edge Routing
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleStartSSEStream}
            disabled={running || isStreaming}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/20 transition-all flex items-center gap-2"
          >
            {running || isStreaming ? (
              <span className="inline-block animate-spin">⌛ Streaming SSE...</span>
            ) : (
              <span>⚡ Start Real-Time SSE Stream</span>
            )}
          </button>
          <button
            onClick={() => onStartDiligence('Financial')}
            disabled={running || isStreaming}
            className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs transition-all flex items-center gap-2"
          >
            ▶ Trigger Sync
          </button>
        </div>
      </div>

      {/* Human Review Gate Interruption Alert Banner */}
      {(state.human_review_required || state.status === 'HUMAN_REVIEW') && (
        <div className="glass-panel p-6 rounded-2xl border-2 border-rose-500/60 bg-rose-950/30 space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">⚠️</span>
              <div>
                <h3 className="text-lg font-bold text-rose-300">Human Review Gate Triggered</h3>
                <p className="text-xs text-rose-200/80">Graph execution paused awaiting expert investment committee decision.</p>
              </div>
            </div>
            <span className="badge-status badge-review">Gate Active</span>
          </div>

          {state.human_review_reasons && state.human_review_reasons.length > 0 && (
            <div className="bg-slate-950/70 p-4 rounded-xl border border-rose-900/50 space-y-1.5">
              <div className="text-xs font-semibold text-rose-400 uppercase tracking-wider">Trigger Reasons:</div>
              <ul className="list-disc list-inside text-xs text-slate-200 space-y-1">
                {state.human_review_reasons.map((reason, idx) => (
                  <li key={idx} className="font-mono text-rose-200">{reason}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Resume Form */}
          <form onSubmit={handleResumeSubmit} className="bg-slate-900/90 p-5 rounded-xl border border-slate-800 space-y-4">
            <div className="flex items-center gap-4 border-b border-slate-800 pb-3">
              <span className="text-xs font-bold text-slate-300 uppercase">Select Action:</span>
              <div className="flex gap-2">
                {(['APPROVE', 'ADD_EVIDENCE', 'REJECT'] as const).map(action => (
                  <button
                    key={action}
                    type="button"
                    onClick={() => setActionType(action)}
                    className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      actionType === action
                        ? action === 'APPROVE'
                          ? 'bg-emerald-600 text-white'
                          : action === 'ADD_EVIDENCE'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-rose-600 text-white'
                        : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {action === 'APPROVE' ? '✓ Approve & Resume' : action === 'ADD_EVIDENCE' ? '+ Add Evidence & Resume' : '✕ Reject Deal'}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Human Feedback / Context Note</label>
              <textarea
                rows={2}
                placeholder="Enter rationale, verification findings, or instructions for the agent network..."
                value={humanFeedback}
                onChange={e => setHumanFeedback(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-xs focus:outline-none focus:border-indigo-500"
              />
            </div>

            {actionType === 'ADD_EVIDENCE' && (
              <div>
                <label className="block text-xs font-semibold text-indigo-300 mb-1">New Evidence Chunk / Document Record</label>
                <textarea
                  rows={2}
                  placeholder="Paste new verified evidence (e.g. audited revenue breakdown, customer contract snippet)..."
                  value={evidenceText}
                  onChange={e => setEvidenceText(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-indigo-800/80 text-slate-100 text-xs focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={submittingAction}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-xs font-bold shadow-md transition-all"
              >
                {submittingAction ? 'Submitting...' : 'Execute Gate Decision & Resume Graph'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* DAG Visualization Grid */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">DAG Node Execution Topology</h3>
          <div className="flex items-center gap-4 text-xs font-semibold">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Completed</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-ping"></span> Active Node</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Human Review</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-slate-700"></span> Pending</span>
          </div>
        </div>

        {/* Pipeline Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {GRAPH_NODES.map(node => {
            const status = getNodeStatus(node.id);
            const iteration = state.iteration_counts[node.id] || 0;
            const evalResult = state.evaluations.find(e => e.target_node === node.id);

            return (
              <div
                key={node.id}
                onClick={() => setSelectedNode(node.id)}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${getCategoryColor(node.category, status)} hover:scale-[1.02]`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    {node.category}
                  </span>
                  {iteration > 0 && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-indigo-950 text-indigo-300 border border-indigo-800">
                      Iter #{iteration}
                    </span>
                  )}
                </div>

                <div className="font-bold text-sm text-white mb-1 flex items-center justify-between">
                  <span>{node.label}</span>
                  {status === 'completed' && <span className="text-emerald-400 text-xs">✓</span>}
                  {status === 'review' && <span className="text-rose-400 text-xs">⚠️</span>}
                </div>

                <p className="text-xs text-slate-400 line-clamp-2 mb-3">{node.description}</p>

                {evalResult && (
                  <div className="mt-2 pt-2 border-t border-slate-800 text-[11px] font-mono flex items-center justify-between">
                    <span className="text-slate-400">Score:</span>
                    <span className={evalResult.overall_pass ? 'text-emerald-400' : 'text-rose-400 font-bold'}>
                      {((evalResult.evidence_coverage_score + evalResult.citation_correctness_score) / 2 * 100).toFixed(0)}%
                    </span>
                  </div>
                )}

                <div className="mt-3 flex justify-between items-center text-[10px] text-slate-400">
                  <span className="font-mono">{node.id}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onRerunNode(node.id);
                    }}
                    className="hover:text-indigo-400 underline font-semibold"
                  >
                    Rerun from here &rarr;
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="glass-panel p-6 rounded-2xl border border-indigo-500/30 space-y-3">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>Inspect Node Execution:</span>
              <span className="font-mono text-indigo-400">{selectedNode}</span>
            </h3>
            <button onClick={() => setSelectedNode(null)} className="text-slate-400 hover:text-white text-sm">✕ Close</button>
          </div>

          {logs.filter(l => l.node_name === selectedNode).length === 0 ? (
            <p className="text-xs text-slate-400">No execution logs recorded yet for this node.</p>
          ) : (
            <div className="space-y-2">
              {logs.filter(l => l.node_name === selectedNode).map((log, i) => (
                <div key={i} className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 text-xs font-mono space-y-2">
                  <div className="flex justify-between text-slate-400">
                    <span>Exec ID: {log.execution_id.slice(0, 8)}</span>
                    <span className="text-emerald-400 font-bold">{log.status}</span>
                  </div>
                  {log.input_summary && (
                    <div>
                      <span className="text-slate-500 block">Input Summary:</span>
                      <pre className="text-slate-300 whitespace-pre-wrap">{JSON.stringify(log.input_summary, null, 2)}</pre>
                    </div>
                  )}
                  {log.output_summary && (
                    <div>
                      <span className="text-slate-500 block">Output Summary:</span>
                      <pre className="text-slate-300 whitespace-pre-wrap">{JSON.stringify(log.output_summary, null, 2)}</pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
