import React, { useState, useEffect } from 'react';
import { DiligenceState, InvestmentSummary, ExecutionLogEntry, DeploymentConfig, CheckpointRecord } from './types';
import { InvestmentsDashboard } from './components/InvestmentsDashboard';
import { GraphVisualizer } from './components/GraphVisualizer';
import { EvidenceExplorer } from './components/EvidenceExplorer';
import { FinancialAnalysisView } from './components/FinancialAnalysisView';
import { ICDebateView } from './components/ICDebateView';
import { MemoView } from './components/MemoView';
import { ComparisonView } from './components/ComparisonView';
import { RiskRadarView } from './components/RiskRadarView';
import { FailureLabView } from './components/FailureLabView';
import { FDEOperationsView } from './components/FDEOperationsView';
import { LoopedDemoPlayer } from './components/LoopedDemoPlayer';
import { CapTableWaterfallView } from './components/CapTableWaterfallView';
import { SensitivityStressView } from './components/SensitivityStressView';
import { DiligenceChatView } from './components/DiligenceChatView';
import { ICAudioDebateView } from './components/ICAudioDebateView';
import { LPTeaserView } from './components/LPTeaserView';

export const App: React.FC = () => {
  const [investments, setInvestments] = useState<InvestmentSummary[]>([]);
  const [selectedInvestmentId, setSelectedInvestmentId] = useState<string | null>(null);
  const [diligenceState, setDiligenceState] = useState<DiligenceState | null>(null);
  const [logs, setLogs] = useState<ExecutionLogEntry[]>([]);
  const [deployments, setDeployments] = useState<DeploymentConfig[]>([]);
  const [selectedDeploymentId, setSelectedDeploymentId] = useState<string>('');
  const [checkpoints, setCheckpoints] = useState<CheckpointRecord[]>([]);
  const [loadingInvestments, setLoadingInvestments] = useState(false);
  const [loadingState, setLoadingState] = useState(false);
  const [graphRunning, setGraphRunning] = useState(false);

  // Top Level Navigation Tab
  const [mainNavTab, setMainNavTab] = useState<
    'workspaces' | 'cap_table' | 'sensitivity' | 'diligence_chat' | 'ic_audio' | 'lp_teaser' | 'comparison' | 'risk_radar' | 'failure_lab' | 'fde_ops'
  >('workspaces');

  // Sub tab within workspace view
  const [activeTab, setActiveTab] = useState<'graph' | 'evidence' | 'financials' | 'ic_debate' | 'memo'>('graph');

  // Fetch deployments list
  const fetchDeployments = async () => {
    try {
      const res = await fetch('/api/v1/deployments');
      if (res.ok) {
        const data = await res.json();
        setDeployments(data);
        if (data.length > 0 && !selectedDeploymentId) {
          setSelectedDeploymentId(data[0].deployment_id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch deployments', err);
    }
  };

  // Fetch investments list
  const fetchInvestments = async () => {
    setLoadingInvestments(true);
    try {
      const res = await fetch('/api/v1/investments');
      if (res.ok) {
        const data = await res.json();
        setInvestments(data);
      }
    } catch (err) {
      console.error('Failed to fetch investments', err);
    } finally {
      setLoadingInvestments(false);
    }
  };

  // Fetch checkpoints
  const fetchCheckpoints = async (invId: string) => {
    try {
      const res = await fetch(`/api/v1/investments/${invId}/diligence/checkpoints`);
      if (res.ok) {
        const data = await res.json();
        setCheckpoints(data);
      }
    } catch (err) {
      console.error('Failed to fetch checkpoints', err);
    }
  };

  // Fetch diligence state & execution logs for selected investment
  const fetchDiligenceState = async (invId: string) => {
    setLoadingState(true);
    try {
      const [stateRes, logsRes, checkpointsRes] = await Promise.all([
        fetch(`/api/v1/investments/${invId}`),
        fetch(`/api/v1/investments/${invId}/diligence/logs`),
        fetch(`/api/v1/investments/${invId}/diligence/checkpoints`)
      ]);

      if (stateRes.ok) {
        const sData = await stateRes.json();
        setDiligenceState(sData);
        if (sData.deployment_id) {
          setSelectedDeploymentId(sData.deployment_id);
        }
      }
      if (logsRes.ok) {
        const lData = await logsRes.json();
        setLogs(lData);
      }
      if (checkpointsRes.ok) {
        const cpData = await checkpointsRes.json();
        setCheckpoints(cpData);
      }
    } catch (err) {
      console.error('Failed to fetch diligence state', err);
    } finally {
      setLoadingState(false);
    }
  };

  useEffect(() => {
    fetchInvestments();
    fetchDeployments();
  }, []);

  useEffect(() => {
    if (selectedInvestmentId) {
      fetchDiligenceState(selectedInvestmentId);
    }
  }, [selectedInvestmentId]);

  // Create investment workspace
  const handleCreateInvestment = async (data: { company_name: string; industry: string; target_round: string; check_size_usd?: number; deployment_id?: string }) => {
    const res = await fetch('/api/v1/investments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (res.ok) {
      const newInv = await res.json();
      await fetchInvestments();
      setSelectedInvestmentId(newInv.investment_id);
      setMainNavTab('workspaces');
    }
  };

  // Start diligence graph execution
  const handleStartDiligence = async (domain: string = 'Financial') => {
    if (!selectedInvestmentId) return;
    setGraphRunning(true);
    try {
      const res = await fetch(`/api/v1/investments/${selectedInvestmentId}/diligence/start?domain=${domain}`, {
        method: 'POST'
      });
      if (res.ok) {
        const newState = await res.json();
        setDiligenceState(newState);
        await fetchDiligenceState(selectedInvestmentId);
      }
    } catch (err) {
      console.error('Failed to start diligence', err);
    } finally {
      setGraphRunning(false);
    }
  };

  // Pause diligence graph execution
  const handlePauseDiligence = async () => {
    if (!selectedInvestmentId) return;
    try {
      const res = await fetch(`/api/v1/investments/${selectedInvestmentId}/diligence/pause`, {
        method: 'POST'
      });
      if (res.ok) {
        const newState = await res.json();
        setDiligenceState(newState);
        await fetchDiligenceState(selectedInvestmentId);
      }
    } catch (err) {
      console.error('Failed to pause diligence', err);
    }
  };

  // Resume diligence graph execution after human review gate
  const handleResumeDiligence = async (action: string, human_feedback?: string, new_evidence?: any[]) => {
    if (!selectedInvestmentId) return;
    setGraphRunning(true);
    try {
      const res = await fetch(`/api/v1/investments/${selectedInvestmentId}/diligence/resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, human_feedback, new_evidence })
      });
      if (res.ok) {
        const newState = await res.json();
        setDiligenceState(newState);
        await fetchDiligenceState(selectedInvestmentId);
      }
    } catch (err) {
      console.error('Failed to resume diligence', err);
    } finally {
      setGraphRunning(false);
    }
  };

  // Retry failed node
  const handleRetryNode = async (failedNode?: string) => {
    if (!selectedInvestmentId) return;
    setGraphRunning(true);
    try {
      const res = await fetch(`/api/v1/investments/${selectedInvestmentId}/diligence/retry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ failed_node: failedNode })
      });
      if (res.ok) {
        const newState = await res.json();
        setDiligenceState(newState);
        await fetchDiligenceState(selectedInvestmentId);
      }
    } catch (err) {
      console.error('Failed to retry node', err);
    } finally {
      setGraphRunning(false);
    }
  };

  // Resolve evidence conflict
  const handleResolveConflict = async (authoritativeEvidenceId: string, conflictId?: string, notes?: string) => {
    if (!selectedInvestmentId) return;
    setGraphRunning(true);
    try {
      const res = await fetch(`/api/v1/investments/${selectedInvestmentId}/diligence/resolve_conflict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          authoritative_evidence_id: authoritativeEvidenceId,
          conflict_id: conflictId,
          resolution_notes: notes
        })
      });
      if (res.ok) {
        const newState = await res.json();
        setDiligenceState(newState);
        await fetchDiligenceState(selectedInvestmentId);
      }
    } catch (err) {
      console.error('Failed to resolve conflict', err);
    } finally {
      setGraphRunning(false);
    }
  };

  // Rerun graph from node
  const handleRerunNode = async (fromNode: string) => {
    if (!selectedInvestmentId) return;
    setGraphRunning(true);
    try {
      const res = await fetch(`/api/v1/investments/${selectedInvestmentId}/diligence/rerun`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_node: fromNode, domain: 'Financial' })
      });
      if (res.ok) {
        const newState = await res.json();
        setDiligenceState(newState);
        await fetchDiligenceState(selectedInvestmentId);
      }
    } catch (err) {
      console.error('Failed to rerun node', err);
    } finally {
      setGraphRunning(false);
    }
  };

  // Upload document
  const handleUploadDocument = async (file: File, docType: string) => {
    if (!selectedInvestmentId) return;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', docType);

    const res = await fetch(`/api/v1/investments/${selectedInvestmentId}/documents`, {
      method: 'POST',
      body: formData
    });
    if (res.ok) {
      await fetchDiligenceState(selectedInvestmentId);
    }
  };

  // Handle tab sync from automated demo player
  const handleDemoTabChange = (tab: string) => {
    switch (tab) {
      case 'deployments':
      case 'fde_ops':
      case 'operations':
        setMainNavTab('fde_ops');
        break;
      case 'failure_lab':
        setMainNavTab('failure_lab');
        break;
      case 'risk_radar':
        setMainNavTab('risk_radar');
        break;
      case 'comparison':
        setMainNavTab('comparison');
        break;
      case 'graph':
        setMainNavTab('workspaces');
        setActiveTab('graph');
        setSelectedInvestmentId((prev) => prev || (investments.length > 0 ? investments[0].investment_id : null));
        break;
      case 'evidence':
        setMainNavTab('workspaces');
        setActiveTab('evidence');
        setSelectedInvestmentId((prev) => prev || (investments.length > 0 ? investments[0].investment_id : null));
        break;
      case 'financials':
        setMainNavTab('workspaces');
        setActiveTab('financials');
        setSelectedInvestmentId((prev) => prev || (investments.length > 0 ? investments[0].investment_id : null));
        break;
      case 'ic_debate':
        setMainNavTab('workspaces');
        setActiveTab('ic_debate');
        setSelectedInvestmentId((prev) => prev || (investments.length > 0 ? investments[0].investment_id : null));
        break;
      case 'memo':
        setMainNavTab('workspaces');
        setActiveTab('memo');
        setSelectedInvestmentId((prev) => prev || (investments.length > 0 ? investments[0].investment_id : null));
        break;
      case 'workspaces':
      default:
        setMainNavTab('workspaces');
        break;
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col">
      {/* Floating Demo Player Bar */}
      <LoopedDemoPlayer onTabChange={handleDemoTabChange} />

      {/* Global Header */}
      <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div
              className="flex items-center gap-3 cursor-pointer"
              onClick={() => {
                setMainNavTab('workspaces');
                setSelectedInvestmentId(null);
              }}
            >
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-white font-extrabold text-sm shadow-md shadow-indigo-600/30">
                AGY
              </div>
              <div>
                <span className="font-extrabold text-base tracking-tight text-white">AI Investment Due Diligence</span>
                <span className="text-[10px] px-2 py-0.5 ml-2 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono">
                  Copilot v1.0
                </span>
              </div>
            </div>

            {/* Top Navigation Tabs */}
            <nav className="hidden md:flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800 overflow-x-auto">
              <button
                onClick={() => setMainNavTab('workspaces')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  mainNavTab === 'workspaces'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <span>🏢</span> Workspaces
              </button>
              <button
                onClick={() => setMainNavTab('cap_table')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  mainNavTab === 'cap_table'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <span>📊</span> Cap Table &amp; Waterfall
              </button>
              <button
                onClick={() => setMainNavTab('sensitivity')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  mainNavTab === 'sensitivity'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <span>⚡</span> Sensitivity &amp; Stress
              </button>
              <button
                onClick={() => setMainNavTab('diligence_chat')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  mainNavTab === 'diligence_chat'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <span>💬</span> Diligence Chat
              </button>
              <button
                onClick={() => setMainNavTab('ic_audio')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  mainNavTab === 'ic_audio'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <span>🎧</span> IC Audio Debate
              </button>
              <button
                onClick={() => setMainNavTab('lp_teaser')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  mainNavTab === 'lp_teaser'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <span>📄</span> LP Teaser
              </button>
              <button
                onClick={() => setMainNavTab('comparison')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  mainNavTab === 'comparison'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <span>⚖️</span> Deal Comparison
              </button>
              <button
                onClick={() => setMainNavTab('risk_radar')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  mainNavTab === 'risk_radar'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <span>🚨</span> Risk Radar
              </button>
              <button
                onClick={() => setMainNavTab('failure_lab')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  mainNavTab === 'failure_lab'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <span>🧪</span> Failure Lab
              </button>
              <button
                onClick={() => setMainNavTab('fde_ops')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  mainNavTab === 'fde_ops'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <span>🚀</span> FDE Ops &amp; Onboarding
              </button>
            </nav>
          </div>

          {selectedInvestmentId && diligenceState && mainNavTab === 'workspaces' && (
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSelectedInvestmentId(null)}
                className="text-xs font-semibold text-slate-400 hover:text-white px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 transition-colors"
              >
                &larr; Back to Dashboard
              </button>
              <div className="text-xs border-l border-slate-800 pl-4 flex items-center gap-2">
                <span className="font-bold text-white">{diligenceState.company_name}</span>
                <span className="text-slate-400 font-mono">({diligenceState.industry})</span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {mainNavTab === 'cap_table' ? (
          <CapTableWaterfallView />
        ) : mainNavTab === 'sensitivity' ? (
          <SensitivityStressView />
        ) : mainNavTab === 'diligence_chat' ? (
          <DiligenceChatView />
        ) : mainNavTab === 'ic_audio' ? (
          <ICAudioDebateView />
        ) : mainNavTab === 'lp_teaser' ? (
          <LPTeaserView />
        ) : mainNavTab === 'comparison' ? (
          <ComparisonView />
        ) : mainNavTab === 'risk_radar' ? (
          <RiskRadarView />
        ) : mainNavTab === 'failure_lab' ? (
          <FailureLabView />
        ) : mainNavTab === 'fde_ops' ? (
          <FDEOperationsView />
        ) : !selectedInvestmentId ? (
          <InvestmentsDashboard
            investments={investments}
            deployments={deployments}
            loading={loadingInvestments}
            onSelectInvestment={setSelectedInvestmentId}
            onCreateInvestment={handleCreateInvestment}
            onRefresh={fetchInvestments}
          />
        ) : loadingState || !diligenceState ? (
          <div className="glass-panel p-16 text-center text-slate-400 rounded-2xl my-12">
            <div className="inline-block animate-spin w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full mb-4"></div>
            <p className="font-semibold text-slate-200">Loading Investment Workspace State...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Workspace Sub-Header Navigation Tabs */}
            <div className="glass-panel p-2 rounded-2xl border border-slate-800 flex flex-wrap gap-2">
              <button
                onClick={() => setActiveTab('graph')}
                className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                  activeTab === 'graph' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`}
              >
                🕸️ Graph Engine Visualizer
              </button>
              <button
                onClick={() => setActiveTab('evidence')}
                className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                  activeTab === 'evidence' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`}
              >
                📁 Evidence Explorer ({diligenceState.evidence_records.length})
              </button>
              <button
                onClick={() => setActiveTab('financials')}
                className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                  activeTab === 'financials' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`}
              >
                📊 Financial Metrics ({diligenceState.financial_metrics.length})
              </button>
              <button
                onClick={() => setActiveTab('ic_debate')}
                className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                  activeTab === 'ic_debate' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`}
              >
                🏛️ IC Debate & Synthesis
              </button>
              <button
                onClick={() => setActiveTab('memo')}
                className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                  activeTab === 'memo' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`}
              >
                📄 Institutional Memo
              </button>
            </div>

            {/* Tab Views */}
            {activeTab === 'graph' && (
              <GraphVisualizer
                state={diligenceState}
                logs={logs}
                deployments={deployments}
                selectedDeploymentId={selectedDeploymentId}
                onSelectDeployment={setSelectedDeploymentId}
                onStartDiligence={handleStartDiligence}
                onResumeDiligence={handleResumeDiligence}
                onRerunNode={handleRerunNode}
                onPauseDiligence={handlePauseDiligence}
                onRetryNode={handleRetryNode}
                onResolveConflict={handleResolveConflict}
                checkpoints={checkpoints}
                running={graphRunning}
              />
            )}

            {activeTab === 'evidence' && (
              <EvidenceExplorer
                documents={diligenceState.documents}
                chunks={diligenceState.document_chunks}
                evidenceRecords={diligenceState.evidence_records}
                onUploadDocument={handleUploadDocument}
              />
            )}

            {activeTab === 'financials' && (
              <FinancialAnalysisView metrics={diligenceState.financial_metrics} />
            )}

            {activeTab === 'ic_debate' && (
              <ICDebateView state={diligenceState} />
            )}

            {activeTab === 'memo' && (
              <MemoView state={diligenceState} evidenceRecords={diligenceState.evidence_records} />
            )}
          </div>
        )}
      </main>
    </div>
  );
};
