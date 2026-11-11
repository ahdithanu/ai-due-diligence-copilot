import React, { useState, useEffect } from 'react';
import {
  DreamingRunResponse,
  StaffEditFeedbackRecord,
  ArtifactComplianceReport,
  HiddenFeeScanResponse,
  OperationalKnowledgeItem,
  ArcaEvalScorecard,
} from '../types';

interface ArcaFirmCommandCenterProps {
  investmentId: string;
  companyName?: string;
}

export const ArcaFirmCommandCenter: React.FC<ArcaFirmCommandCenterProps> = ({
  investmentId,
  companyName = 'Acme SaaS AI',
}) => {
  const [activeTab, setActiveTab] = useState<
    'evals' | 'knowledge' | 'dreaming' | 'staff_feedback' | 'compliance' | 'hidden_fees'
  >('evals');

  // Operational Knowledge State
  const [knowledgeItems, setKnowledgeItems] = useState<OperationalKnowledgeItem[]>([]);
  const [loadingKnowledge, setLoadingKnowledge] = useState(false);
  const [editingItem, setEditingItem] = useState<OperationalKnowledgeItem | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [savingKnowledge, setSavingKnowledge] = useState(false);

  // Dreaming State
  const [dreamingData, setDreamingData] = useState<DreamingRunResponse | null>(null);
  const [loadingDreaming, setLoadingDreaming] = useState(false);
  const [runningDreaming, setRunningDreaming] = useState(false);

  // Staff Feedback State
  const [staffEdits, setStaffEdits] = useState<StaffEditFeedbackRecord[]>([]);
  const [loadingStaffEdits, setLoadingStaffEdits] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [newTargetField, setNewTargetField] = useState('gross_margin_target');
  const [newOriginalVal, setNewOriginalVal] = useState('82.5%');
  const [newAdjustedVal, setNewAdjustedVal] = useState('78.0%');
  const [newReasonWhy, setNewReasonWhy] = useState('');
  const [newEditorRole, setNewEditorRole] = useState('Senior Deal Partner');
  const [submittingStaffEdit, setSubmittingStaffEdit] = useState(false);
  const [staffEditError, setStaffEditError] = useState('');

  // Compliance Verifier State
  const [artifactName, setArtifactName] = useState('acme_ic_memo_v2.pdf');
  const [artifactContent, setArtifactContent] = useState(
    'Acme SaaS AI demonstrated $9.35M in ARR [rag-chunk-101] with 80% net retention [rag-chunk-102]. Target gross margins sit at 78% after customer onboarding costs.'
  );
  const [complianceReport, setComplianceReport] = useState<ArtifactComplianceReport | null>(null);
  const [verifyingArtifact, setVerifyingArtifact] = useState(false);

  // Hidden Fee Scanner State
  const [feeScanData, setFeeScanData] = useState<HiddenFeeScanResponse | null>(null);
  const [loadingFeeScan, setLoadingFeeScan] = useState(false);

  // Golden Eval Suite State
  const [evalScorecard, setEvalScorecard] = useState<ArcaEvalScorecard | null>(null);
  const [runningEvals, setRunningEvals] = useState(false);

  // =========================================================================
  // API Fetchers
  // =========================================================================

  const fetchKnowledge = async () => {
    setLoadingKnowledge(true);
    try {
      const res = await fetch('/api/v1/operational-knowledge');
      if (res.ok) {
        const data = await res.json();
        setKnowledgeItems(data);
      }
    } catch (err) {
      console.error('Failed to load operational knowledge', err);
    } finally {
      setLoadingKnowledge(false);
    }
  };

  const saveKnowledge = async () => {
    if (!editingItem) return;
    setSavingKnowledge(true);
    try {
      const url = `/api/v1/operational-knowledge/${editingItem.id}?title=${encodeURIComponent(
        editTitle
      )}&content_markdown=${encodeURIComponent(editContent)}&editor=Deal%20Lead`;
      const res = await fetch(url, { method: 'PUT' });
      if (res.ok) {
        setEditingItem(null);
        await fetchKnowledge();
      }
    } catch (err) {
      console.error('Failed to update knowledge item', err);
    } finally {
      setSavingKnowledge(false);
    }
  };

  const fetchDreaming = async () => {
    setLoadingDreaming(true);
    try {
      const res = await fetch(
        `/api/v1/investments/${investmentId}/dreaming/latest?company_name=${encodeURIComponent(
          companyName
        )}`
      );
      if (res.ok) {
        const data = await res.json();
        setDreamingData(data);
      }
    } catch (err) {
      console.error('Failed to fetch dreaming state', err);
    } finally {
      setLoadingDreaming(false);
    }
  };

  const triggerDreaming = async () => {
    setRunningDreaming(true);
    try {
      const res = await fetch(
        `/api/v1/investments/${investmentId}/dreaming/run?company_name=${encodeURIComponent(
          companyName
        )}`,
        { method: 'POST' }
      );
      if (res.ok) {
        const data = await res.json();
        setDreamingData(data);
      }
    } catch (err) {
      console.error('Failed to run dreaming reflection', err);
    } finally {
      setRunningDreaming(false);
    }
  };

  const fetchStaffEdits = async () => {
    setLoadingStaffEdits(true);
    try {
      const res = await fetch(`/api/v1/investments/${investmentId}/staff-feedback`);
      if (res.ok) {
        const data = await res.json();
        setStaffEdits(data);
      }
    } catch (err) {
      console.error('Failed to fetch staff feedback', err);
    } finally {
      setLoadingStaffEdits(false);
    }
  };

  const submitStaffEdit = async () => {
    if (!newReasonWhy.trim()) {
      setStaffEditError('Arca Operating Principle: Every staff edit must have a clear "Why" rationale.');
      return;
    }
    setStaffEditError('');
    setSubmittingStaffEdit(true);
    try {
      const res = await fetch(`/api/v1/investments/${investmentId}/staff-feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_field: newTargetField,
          agent_original_value: newOriginalVal,
          human_adjusted_value: newAdjustedVal,
          reason_why: newReasonWhy,
          editor_role: newEditorRole,
        }),
      });
      if (res.ok) {
        setShowEditModal(false);
        setNewReasonWhy('');
        await fetchStaffEdits();
      } else {
        const errJson = await res.json();
        setStaffEditError(errJson.detail || 'Failed to record staff feedback');
      }
    } catch (err) {
      console.error('Failed to record staff feedback', err);
      setStaffEditError('Network error recording feedback');
    } finally {
      setSubmittingStaffEdit(false);
    }
  };

  const verifyArtifact = async () => {
    setVerifyingArtifact(true);
    try {
      const res = await fetch('/api/v1/investments/verify-artifact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          artifact_name: artifactName,
          content: artifactContent,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setComplianceReport(data);
      }
    } catch (err) {
      console.error('Failed to verify artifact', err);
    } finally {
      setVerifyingArtifact(false);
    }
  };

  const scanHiddenFees = async () => {
    setLoadingFeeScan(true);
    try {
      const res = await fetch(`/api/v1/investments/${investmentId}/hidden-fees`);
      if (res.ok) {
        const data = await res.json();
        setFeeScanData(data);
      }
    } catch (err) {
      console.error('Failed to scan hidden fees', err);
    } finally {
      setLoadingFeeScan(false);
    }
  };

  const runEvalSuite = async () => {
    setRunningEvals(true);
    try {
      const res = await fetch('/api/v1/evals/arca/run');
      if (res.ok) {
        const data = await res.json();
        setEvalScorecard(data);
      }
    } catch (err) {
      console.error('Failed to run eval suite', err);
    } finally {
      setRunningEvals(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchKnowledge();
    fetchDreaming();
    fetchStaffEdits();
    scanHiddenFees();
    runEvalSuite();
  }, [investmentId, companyName]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-indigo-900/50 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none text-8xl font-black">
          ARCA
        </div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-indigo-500/20 border border-indigo-400/30 rounded-full text-indigo-300 text-xs font-semibold uppercase tracking-wider">
                Arca AI-Native Firm Core
              </span>
              <span className="text-xs text-slate-400">
                Target: <strong className="text-white">{companyName}</strong> ({investmentId})
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white mt-2 tracking-tight">
              AI-Native Firm Operations &amp; Golden Eval Benchmark Suite
            </h1>
            <p className="text-slate-300 text-sm mt-1 max-w-3xl">
              Modeled after Arca&apos;s $64M AI-native architecture: autonomous deal &ldquo;dreaming&rdquo; consolidation,
              mandatory staff-edit feedback loops, dual-layer edge artifact compliance, and non-fiduciary fee scanning.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={runEvalSuite}
              disabled={runningEvals}
              className="px-4 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-900/30 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              <span>{runningEvals ? '⚡ Running Benchmark...' : '🧪 Run Golden Eval Suite'}</span>
            </button>
            <button
              onClick={triggerDreaming}
              disabled={runningDreaming}
              className="px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-purple-900/30 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              <span>{runningDreaming ? '🌙 Dreaming...' : '🌙 Trigger 30-Day Dreaming'}</span>
            </button>
          </div>
        </div>

        {/* Top-level Key Performance Indicators */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-6 pt-6 border-t border-slate-800/80">
          <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Overall Eval Pass Rate</div>
            <div className="text-xl font-extrabold text-emerald-400 mt-0.5">
              {evalScorecard ? `${evalScorecard.overall_firm_eval_pass_rate_pct.toFixed(1)}%` : '--'}
            </div>
            <div className="text-[10px] text-slate-500">
              {evalScorecard ? `${evalScorecard.passed_cases}/${evalScorecard.total_test_cases} tests passing` : 'Loading...'}
            </div>
          </div>
          <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Agent Readiness Score</div>
            <div className="text-xl font-extrabold text-cyan-400 mt-0.5">
              {dreamingData ? `${dreamingData.agent_readiness_score.toFixed(1)}%` : '--'}
            </div>
            <div className="text-[10px] text-slate-500">Autonomous deal horizon</div>
          </div>
          <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Hidden Fee Leakage</div>
            <div className="text-xl font-extrabold text-rose-400 mt-0.5">
              {feeScanData ? `$${(feeScanData.total_annual_drag_usd / 1000).toFixed(0)}k/yr` : '--'}
            </div>
            <div className="text-[10px] text-slate-500">
              {feeScanData ? `${feeScanData.findings.length} contractual traps` : 'Scanning...'}
            </div>
          </div>
          <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Staff Feedback Traces</div>
            <div className="text-xl font-extrabold text-purple-400 mt-0.5">
              {staffEdits.length}
            </div>
            <div className="text-[10px] text-slate-500">100% paired with &ldquo;Why&rdquo;</div>
          </div>
          <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Operational Knowledge</div>
            <div className="text-xl font-extrabold text-amber-400 mt-0.5">
              {knowledgeItems.length} Guidelines
            </div>
            <div className="text-[10px] text-slate-500">Cited across underwriting</div>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('evals')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'evals'
              ? 'bg-emerald-600 text-white shadow-md shadow-emerald-900/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <span>🧪</span> Golden Benchmark Eval Suite
        </button>
        <button
          onClick={() => setActiveTab('knowledge')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'knowledge'
              ? 'bg-amber-600 text-white shadow-md shadow-amber-900/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <span>📚</span> Operational Knowledge Base
        </button>
        <button
          onClick={() => setActiveTab('dreaming')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'dreaming'
              ? 'bg-purple-600 text-white shadow-md shadow-purple-900/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <span>🌙</span> Deal &ldquo;Dreaming&rdquo; Reflection
        </button>
        <button
          onClick={() => setActiveTab('staff_feedback')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'staff_feedback'
              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-900/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <span>✍️</span> Staff Edits &amp; Eval Pipeline
        </button>
        <button
          onClick={() => setActiveTab('compliance')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'compliance'
              ? 'bg-cyan-600 text-white shadow-md shadow-cyan-900/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <span>🛡️</span> Edge Artifact Compliance Verifier
        </button>
        <button
          onClick={() => setActiveTab('hidden_fees')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'hidden_fees'
              ? 'bg-rose-600 text-white shadow-md shadow-rose-900/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <span>🔎</span> Hidden Fee &amp; Trap Scanner
        </button>
      </div>

      {/* =========================================================================
          TAB 1: Golden Benchmark Eval Suite
         ========================================================================= */}
      {activeTab === 'evals' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>🧪</span> Arca AI-Native Benchmark &amp; Regression Scorecard
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Automated test harnesses validating Edge Compliance, Hidden Fee Detection, Staff Feedback Loops, and Dreaming Memory.
                </p>
              </div>
              <button
                onClick={runEvalSuite}
                disabled={runningEvals}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl transition-all shadow-md disabled:opacity-50"
              >
                {runningEvals ? 'Running Tests...' : 'Re-run All Benchmark Tests'}
              </button>
            </div>

            {evalScorecard ? (
              <div className="space-y-6">
                {/* Score Breakdown Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400 font-semibold">Edge Compliance Score</div>
                    <div className="text-2xl font-black text-cyan-400 mt-1">
                      {evalScorecard.edge_artifact_compliance_score_pct.toFixed(0)}%
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                      <div
                        className="bg-cyan-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${evalScorecard.edge_artifact_compliance_score_pct}%` }}
                      />
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">PII, Wire &amp; SEC promissory defense</div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400 font-semibold">Hidden Fee Detection</div>
                    <div className="text-2xl font-black text-rose-400 mt-1">
                      {evalScorecard.hidden_fee_detection_score_pct.toFixed(0)}%
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                      <div
                        className="bg-rose-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${evalScorecard.hidden_fee_detection_score_pct}%` }}
                      />
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">Related-party &amp; senior ratchets</div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400 font-semibold">Staff Feedback Loop</div>
                    <div className="text-2xl font-black text-purple-400 mt-1">
                      {evalScorecard.staff_feedback_capture_score_pct.toFixed(0)}%
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                      <div
                        className="bg-purple-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${evalScorecard.staff_feedback_capture_score_pct}%` }}
                      />
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">&ldquo;Why&rdquo; rationale enforcement</div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400 font-semibold">Dreaming Synthesis</div>
                    <div className="text-2xl font-black text-amber-400 mt-1">
                      {evalScorecard.dreaming_synthesis_score_pct.toFixed(0)}%
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                      <div
                        className="bg-amber-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${evalScorecard.dreaming_synthesis_score_pct}%` }}
                      />
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">30-day horizon consolidation</div>
                  </div>
                </div>

                {/* Test Cases Table */}
                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-950 text-slate-400 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-800">
                      <tr>
                        <th className="py-3 px-4">Test Case ID</th>
                        <th className="py-3 px-4">Category</th>
                        <th className="py-3 px-4">Scenario</th>
                        <th className="py-3 px-4">Status</th>
                        <th className="py-3 px-4">Score</th>
                        <th className="py-3 px-4">Verification Details</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-900/60">
                      {evalScorecard.case_details.map((tc) => (
                        <tr key={tc.case_id} className="hover:bg-slate-800/40">
                          <td className="py-3 px-4 font-mono text-slate-300">{tc.case_id}</td>
                          <td className="py-3 px-4">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 border border-slate-700 text-slate-300">
                              {tc.category}
                            </span>
                          </td>
                          <td className="py-3 px-4 font-medium text-white">{tc.scenario}</td>
                          <td className="py-3 px-4">
                            <span
                              className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                                tc.passed
                                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                  : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              }`}
                            >
                              {tc.passed ? 'PASSED' : 'FAILED'}
                            </span>
                          </td>
                          <td className="py-3 px-4 font-mono font-bold text-slate-200">
                            {tc.score_pct.toFixed(0)}%
                          </td>
                          <td className="py-3 px-4 text-slate-400 max-w-md">{tc.details}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500 text-sm">
                No evaluation scorecard available. Click &ldquo;Re-run All Benchmark Tests&rdquo; above.
              </div>
            )}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 2: Operational Knowledge Base (First-Class UI Tab)
         ========================================================================= */}
      {activeTab === 'knowledge' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>📚</span> Operational Underwriting Guidelines &amp; Knowledge Base
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Curated firm guidelines directly cited by autonomous agents during investment analysis.
                  Staff edits here update live prompt grounding.
                </p>
              </div>
              <button
                onClick={fetchKnowledge}
                disabled={loadingKnowledge}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition-all"
              >
                {loadingKnowledge ? 'Refreshing...' : 'Refresh Guidelines'}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {knowledgeItems.map((item) => (
                <div
                  key={item.id}
                  className="bg-slate-950 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="px-2 py-0.5 bg-amber-500/10 border border-amber-500/20 text-amber-300 rounded text-[10px] font-mono font-bold">
                        {item.category}
                      </span>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {item.citations_count} agent citations
                      </span>
                    </div>
                    <h4 className="text-sm font-bold text-white mb-2">{item.title}</h4>
                    <div className="text-xs text-slate-400 font-mono bg-slate-900 p-2.5 rounded-lg border border-slate-800 max-h-36 overflow-y-auto whitespace-pre-wrap">
                      {item.content_markdown}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4 mt-4 border-t border-slate-900 text-[11px] text-slate-500">
                    <div>
                      Last edited by <span className="text-slate-300">{item.last_editor}</span>
                    </div>
                    <button
                      onClick={() => {
                        setEditingItem(item);
                        setEditTitle(item.title);
                        setEditContent(item.content_markdown);
                      }}
                      className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition-all"
                    >
                      Edit Guideline
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Guideline Editor Modal */}
          {editingItem && (
            <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-2xl w-full space-y-4 shadow-2xl">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white">
                    Edit Guideline: {editingItem.filename}
                  </h3>
                  <button
                    onClick={() => setEditingItem(null)}
                    className="text-slate-400 hover:text-white text-lg font-bold"
                  >
                    &times;
                  </button>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Title</label>
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Guideline Markdown Content
                  </label>
                  <textarea
                    rows={10}
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    onClick={() => setEditingItem(null)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveKnowledge}
                    disabled={savingKnowledge}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg shadow-md disabled:opacity-50"
                  >
                    {savingKnowledge ? 'Saving...' : 'Save & Propagate to Agents'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 3: Deal "Dreaming" Reflection
         ========================================================================= */}
      {activeTab === 'dreaming' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>🌙</span> Deal Memory &ldquo;Dreaming&rdquo; Reflection Engine
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Consolidates 30 days of asynchronous deal signals, verifies structural invariants,
                  resolves conflicting statements, and scores autonomous agent readiness.
                </p>
              </div>
              <button
                onClick={triggerDreaming}
                disabled={runningDreaming}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold rounded-xl transition-all shadow-md shadow-purple-900/30 disabled:opacity-50"
              >
                {runningDreaming ? 'Consolidating Deal State...' : 'Trigger Immediate Dreaming Run'}
              </button>
            </div>

            {dreamingData ? (
              <div className="space-y-6">
                {/* Metrics Bar */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400 font-semibold">Autonomous Readiness Score</div>
                    <div className="text-3xl font-black text-purple-400 mt-1">
                      {dreamingData.agent_readiness_score.toFixed(1)}%
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">
                      Target confidence for unattended long-horizon handoffs
                    </div>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400 font-semibold">Signals Consolidated</div>
                    <div className="text-3xl font-black text-cyan-400 mt-1">
                      {dreamingData.signals_consolidated_count} Signals
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">
                      Emails, data room revisions, partner calls &amp; banking events
                    </div>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400 font-semibold">Last Dreamed Reflection</div>
                    <div className="text-sm font-mono text-white mt-2">
                      {new Date(dreamingData.last_dreamed_at).toLocaleString()}
                    </div>
                    <div className="text-[10px] text-emerald-400 mt-1">State persisted to durable disk</div>
                  </div>
                </div>

                {/* Synthesized State */}
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-5">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                    Synthesized Deal State of the World
                  </h4>
                  <div className="text-xs text-slate-300 font-mono bg-slate-900 p-4 rounded-lg border border-slate-800/80 whitespace-pre-wrap">
                    {dreamingData.synthesized_deal_state_summary}
                  </div>
                </div>

                {/* Invariants & Contradictions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-5">
                    <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <span>🔒</span> Key Invariants Updated ({dreamingData.key_invariants_updated.length})
                    </h4>
                    <ul className="space-y-2">
                      {dreamingData.key_invariants_updated.map((inv, idx) => (
                        <li
                          key={idx}
                          className="text-xs text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800 flex items-start gap-2"
                        >
                          <span className="text-emerald-400 font-bold">✓</span>
                          <span>{inv}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-5">
                    <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <span>⚖️</span> Resolved Contradictions ({dreamingData.resolved_contradictions.length})
                    </h4>
                    <ul className="space-y-2">
                      {dreamingData.resolved_contradictions.map((rc, idx) => (
                        <li
                          key={idx}
                          className="text-xs text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800 flex items-start gap-2"
                        >
                          <span className="text-amber-400 font-bold">↔</span>
                          <span>{rc}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Recommended Horizon Actions */}
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-5">
                  <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-3">
                    Recommended Next-Horizon Autonomous Actions
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {dreamingData.recommended_next_horizon_actions.map((act, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg bg-indigo-950/30 border border-indigo-900/40 text-xs text-indigo-200"
                      >
                        <span className="font-bold text-indigo-400 block mb-1">Step {idx + 1}</span>
                        {act}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500 text-sm">
                No dreaming state consolidated yet. Click &ldquo;Trigger Immediate Dreaming Run&rdquo; above.
              </div>
            )}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 4: Staff Edits & Eval Pipeline ("Every Staff Edit Has a Why")
         ========================================================================= */}
      {activeTab === 'staff_feedback' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>✍️</span> Staff Adjustment Feedback &amp; Continuous Eval Pipeline
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  &ldquo;Every staff edit has a why.&rdquo; Captures human overrides with structured rationale,
                  creating automated regression test cases in the golden evaluation dataset.
                </p>
              </div>
              <button
                onClick={() => setShowEditModal(true)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition-all shadow-md shadow-indigo-900/30"
              >
                + Record Human Adjustment
              </button>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Candidate ID</th>
                    <th className="py-3 px-4">Target Field</th>
                    <th className="py-3 px-4">Agent Value</th>
                    <th className="py-3 px-4">Human Adjusted</th>
                    <th className="py-3 px-4">Mandatory &ldquo;Why&rdquo; Rationale</th>
                    <th className="py-3 px-4">Editor</th>
                    <th className="py-3 px-4">Eval Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/60">
                  {staffEdits.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/40">
                      <td className="py-3 px-4 font-mono text-indigo-400 font-semibold">
                        {item.eval_candidate_id}
                      </td>
                      <td className="py-3 px-4 font-bold text-white">{item.target_field}</td>
                      <td className="py-3 px-4 font-mono text-slate-400">
                        {typeof item.agent_original_value === 'object'
                          ? JSON.stringify(item.agent_original_value)
                          : String(item.agent_original_value)}
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-emerald-400">
                        {typeof item.human_adjusted_value === 'object'
                          ? JSON.stringify(item.human_adjusted_value)
                          : String(item.human_adjusted_value)}
                      </td>
                      <td className="py-3 px-4 text-slate-300 max-w-sm">
                        <span className="italic">&ldquo;{item.reason_why}&rdquo;</span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">{item.editor_role}</td>
                      <td className="py-3 px-4">
                        <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {staffEdits.length === 0 && (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-slate-500">
                        No staff adjustments recorded yet. Click &ldquo;Record Human Adjustment&rdquo; to log one.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Record Feedback Modal */}
          {showEditModal && (
            <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <span>✍️</span> Record Staff Adjustment (&ldquo;Why&rdquo; Required)
                  </h3>
                  <button
                    onClick={() => setShowEditModal(false)}
                    className="text-slate-400 hover:text-white text-lg font-bold"
                  >
                    &times;
                  </button>
                </div>

                {staffEditError && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs font-semibold">
                    {staffEditError}
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Target Field</label>
                  <input
                    type="text"
                    value={newTargetField}
                    onChange={(e) => setNewTargetField(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">
                      Agent Original Value
                    </label>
                    <input
                      type="text"
                      value={newOriginalVal}
                      onChange={(e) => setNewOriginalVal(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">
                      Human Adjusted Value
                    </label>
                    <input
                      type="text"
                      value={newAdjustedVal}
                      onChange={(e) => setNewAdjustedVal(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Mandatory Reason &ldquo;Why&rdquo; (Required for Eval Pipeline)
                  </label>
                  <textarea
                    rows={4}
                    placeholder="E.g., Target gross margins contracted 4% in Q3; normalized peer multiples dictate 12.0x ceiling."
                    value={newReasonWhy}
                    onChange={(e) => setNewReasonWhy(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Editor Role</label>
                  <select
                    value={newEditorRole}
                    onChange={(e) => setNewEditorRole(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Senior Deal Partner">Senior Deal Partner</option>
                    <option value="Deal Lead">Deal Lead</option>
                    <option value="Principal Underwriter">Principal Underwriter</option>
                    <option value="Investment Committee Member">Investment Committee Member</option>
                  </select>
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    onClick={() => setShowEditModal(false)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={submitStaffEdit}
                    disabled={submittingStaffEdit}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg shadow-md disabled:opacity-50"
                  >
                    {submittingStaffEdit ? 'Submitting...' : 'Record Feedback &amp; Pipe to Eval'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 5: Dual-Layer Edge Artifact Compliance Verifier
         ========================================================================= */}
      {activeTab === 'compliance' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>🛡️</span> Dual-Layer Edge Artifact Compliance Verifier
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Inspects generated memos, LP teasers, and financial spreads before client release.
                  Enforces deterministic regex PII/wire scrubbing and SEC promissory return defense.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setArtifactName('wire_leak_memo.txt');
                    setArtifactContent(
                      'Please initiate a deposit to routing number 021000021 account 998877665544 for tax clearance.'
                    );
                  }}
                  className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] font-mono"
                >
                  Load Wire PII Test
                </button>
                <button
                  onClick={() => {
                    setArtifactName('promissory_teaser.txt');
                    setArtifactContent(
                      'We guarantee a minimum 4.0x MOIC with zero risk of capital loss in this investment.'
                    );
                  }}
                  className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] font-mono"
                >
                  Load Promissory Test
                </button>
                <button
                  onClick={() => {
                    setArtifactName('clean_ic_pack.txt');
                    setArtifactContent(
                      'Acme SaaS AI posted $9.35M in ARR [rag-chunk-101] with 80% gross margin [rag-chunk-102]. The model indicates an estimated 3.2x MOIC base case.'
                    );
                  }}
                  className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] font-mono"
                >
                  Load Compliant Test
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Input Area */}
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Artifact Filename</label>
                  <input
                    type="text"
                    value={artifactName}
                    onChange={(e) => setArtifactName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">
                    Artifact Text Content to Inspect
                  </label>
                  <textarea
                    rows={8}
                    value={artifactContent}
                    onChange={(e) => setArtifactContent(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <button
                  onClick={verifyArtifact}
                  disabled={verifyingArtifact}
                  className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded-xl transition-all shadow-md shadow-cyan-900/30 disabled:opacity-50"
                >
                  {verifyingArtifact ? 'Scanning Compliance Invariants...' : 'Run Edge Artifact Verification'}
                </button>
              </div>

              {/* Report Output */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                      Verification Outcome
                    </span>
                    {complianceReport && (
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-black ${
                          complianceReport.passed
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        {complianceReport.passed ? '✓ PASSED COMPLIANCE' : '✕ BLOCKED RELEASE'}
                      </span>
                    )}
                  </div>

                  {complianceReport ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-3">
                        <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                          <div className="text-[11px] text-slate-400">PII / Wire Violations</div>
                          <div
                            className={`text-xl font-bold mt-0.5 ${
                              complianceReport.pii_violations_count > 0 ? 'text-rose-400' : 'text-emerald-400'
                            }`}
                          >
                            {complianceReport.pii_violations_count}
                          </div>
                        </div>
                        <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                          <div className="text-[11px] text-slate-400">Promissory Claims</div>
                          <div
                            className={`text-xl font-bold mt-0.5 ${
                              complianceReport.promissory_claims_count > 0 ? 'text-rose-400' : 'text-emerald-400'
                            }`}
                          >
                            {complianceReport.promissory_claims_count}
                          </div>
                        </div>
                      </div>

                      {complianceReport.violations.length > 0 && (
                        <div>
                          <div className="text-[11px] text-rose-400 font-bold mb-1">Detected Violations:</div>
                          <ul className="space-y-1">
                            {complianceReport.violations.map((v, idx) => (
                              <li
                                key={idx}
                                className="text-xs text-rose-300 bg-rose-950/30 border border-rose-900/40 p-2 rounded"
                              >
                                {v}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <div>
                        <div className="text-[11px] text-slate-400 font-bold mb-1">
                          Sanitized / Redacted Deliverable Content:
                        </div>
                        <div className="text-xs font-mono text-emerald-300 bg-slate-900 p-3 rounded-lg border border-slate-800 max-h-36 overflow-y-auto whitespace-pre-wrap">
                          {complianceReport.sanitized_content}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-16 text-slate-500 text-xs">
                      Run verification on an artifact above to inspect PII and compliance findings.
                    </div>
                  )}
                </div>

                {complianceReport && (
                  <div className="text-[10px] text-slate-500 text-right pt-2 border-t border-slate-900 mt-4">
                    Audit Timestamp: {new Date(complianceReport.audit_timestamp).toLocaleTimeString()}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 6: Hidden Fee, Cap Table Trap & Non-Fiduciary Conflict Scanner
         ========================================================================= */}
      {activeTab === 'hidden_fees' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>🔎</span> Hidden Fee, Cap Table Trap &amp; Non-Fiduciary Scanner
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Detects hidden monitoring retainers, non-fiduciary disclaimers, and senior liquidation ratchets
                  buried in purchase agreements and side letters.
                </p>
              </div>
              <button
                onClick={scanHiddenFees}
                disabled={loadingFeeScan}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl transition-all shadow-md shadow-rose-900/30 disabled:opacity-50"
              >
                {loadingFeeScan ? 'Scanning Agreements...' : 'Re-scan Data Room Documents'}
              </button>
            </div>

            {feeScanData ? (
              <div className="space-y-6">
                {/* Drag Banner */}
                <div className="bg-rose-950/30 border border-rose-900/50 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="text-xs font-semibold text-rose-300 uppercase tracking-wider">
                      Total Annual Financial Drag Identified
                    </div>
                    <div className="text-3xl font-black text-rose-400 mt-1">
                      ${feeScanData.total_annual_drag_usd.toLocaleString()} / year
                    </div>
                    <p className="text-xs text-rose-200/80 mt-1">
                      Unchecked fees diminish baseline returns by 180 to 240 basis points over the hold period.
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold border ${
                        feeScanData.has_non_fiduciary_language
                          ? 'bg-rose-900/60 border-rose-700 text-rose-200'
                          : 'bg-emerald-950 border-emerald-800 text-emerald-300'
                      }`}
                    >
                      {feeScanData.has_non_fiduciary_language
                        ? '⚠️ Non-Fiduciary Clause Found'
                        : '✓ Fiduciary Covenants Clear'}
                    </div>
                    <div
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold border ${
                        feeScanData.has_senior_ratchet
                          ? 'bg-rose-900/60 border-rose-700 text-rose-200'
                          : 'bg-emerald-950 border-emerald-800 text-emerald-300'
                      }`}
                    >
                      {feeScanData.has_senior_ratchet
                        ? '⚠️ Senior Ratchet Detected'
                        : '✓ Standard 1.0x Liquidation'}
                    </div>
                  </div>
                </div>

                {/* Findings Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {feeScanData.findings.map((f) => (
                    <div
                      key={f.id}
                      className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-3 flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between">
                          <span
                            className={`px-2.5 py-1 rounded text-[10px] font-bold ${
                              f.severity === 'CRITICAL'
                                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            }`}
                          >
                            {f.severity} : {f.category}
                          </span>
                          {f.annual_drag_usd > 0 && (
                            <span className="text-xs font-mono font-bold text-rose-400">
                              +${f.annual_drag_usd.toLocaleString()}/yr drag
                            </span>
                          )}
                        </div>

                        <div className="text-[11px] text-slate-400 font-mono mt-2">
                          Source: <strong className="text-slate-200">{f.document_source}</strong>
                        </div>

                        <div className="text-xs font-mono text-slate-300 bg-slate-900 p-3 rounded-lg border border-slate-800/80 mt-2 italic">
                          &ldquo;{f.clause_text}&rdquo;
                        </div>
                      </div>

                      <div className="p-3 bg-indigo-950/30 border border-indigo-900/40 rounded-lg text-xs text-indigo-200">
                        <span className="font-bold text-indigo-400 block mb-0.5">Remediation Action:</span>
                        {f.recommendation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500 text-sm">
                No fee scanning results available. Click &ldquo;Re-scan Data Room Documents&rdquo; above.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
