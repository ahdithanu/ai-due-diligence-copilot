import React, { useState, useEffect } from 'react';
import {
  LongHorizonSpaceResponse,
  SignalType,
  SignalSource,
  PartnerActionItem,
} from '../types';

interface LongHorizonDealSpaceViewProps {
  investmentId: string;
  companyName?: string;
}

export const LongHorizonDealSpaceView: React.FC<LongHorizonDealSpaceViewProps> = ({
  investmentId,
  companyName = 'Acme SaaS AI',
}) => {
  const [data, setData] = useState<LongHorizonSpaceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'inbox' | 'signals' | 'constraints' | 'mandates'>('inbox');

  // Modals
  const [showSignalModal, setShowSignalModal] = useState(false);
  const [sigTitle, setSigTitle] = useState('');
  const [sigType, setSigType] = useState<SignalType>('FOUNDER_EMAIL_RECEIVED');
  const [sigPayloadSender, setSigPayloadSender] = useState('elena@acme.ai');

  const [showConstraintModal, setShowConstraintModal] = useState(false);
  const [constraintCategory, setConstraintCategory] = useState('EQUITY_STRUCTURE');
  const [constraintRule, setConstraintRule] = useState('');
  const [constraintSource, setConstraintSource] = useState('Partner Negotiation Call');

  const [showMandateModal, setShowMandateModal] = useState(false);
  const [mandateName, setMandateName] = useState('');
  const [mandateDesc, setMandateDesc] = useState('');

  const [actionProcessing, setActionProcessing] = useState<string | null>(null);

  const fetchSpace = async () => {
    setLoading(true);
    try {
      const url = `/api/v1/investments/${investmentId}/long-horizon/space?company_name=${encodeURIComponent(
        companyName
      )}`;
      const res = await fetch(url);
      if (res.ok) {
        const json: LongHorizonSpaceResponse = await res.json();
        setData(json);
      }
    } catch (err) {
      console.error('Failed to load long-horizon deal space', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSpace();
  }, [investmentId, companyName]);

  const handleResolveAction = async (actionId: string, approved: boolean) => {
    setActionProcessing(actionId);
    try {
      const res = await fetch(
        `/api/v1/investments/${investmentId}/long-horizon/actions/${actionId}/resolve`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            approved,
            resolution_notes: approved ? 'Approved via 1-Click Executive Decision' : 'Rejected by Deal Partner',
          }),
        }
      );
      if (res.ok) {
        await fetchSpace();
      }
    } catch (err) {
      console.error('Failed to resolve partner action', err);
    } finally {
      setActionProcessing(null);
    }
  };

  const handleSimulateSignal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sigTitle.trim()) return;
    try {
      const res = await fetch(`/api/v1/investments/${investmentId}/long-horizon/signals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signal_type: sigType,
          source: 'EXTERNAL_WORLD',
          title: sigTitle,
          payload: { sender: sigPayloadSender, timestamp: new Date().toISOString() },
        }),
      });
      if (res.ok) {
        setSigTitle('');
        setShowSignalModal(false);
        await fetchSpace();
        setActiveTab('inbox');
      }
    } catch (err) {
      console.error('Failed to ingest world signal', err);
    }
  };

  const handleAddConstraint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!constraintRule.trim()) return;
    try {
      const res = await fetch(`/api/v1/investments/${investmentId}/long-horizon/constraints`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: constraintCategory,
          rule_text: constraintRule,
          source: constraintSource,
        }),
      });
      if (res.ok) {
        setConstraintRule('');
        setShowConstraintModal(false);
        await fetchSpace();
      }
    } catch (err) {
      console.error('Failed to add durable constraint', err);
    }
  };

  const handleAddMandate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mandateName.trim()) return;
    try {
      const res = await fetch('/api/v1/investments/long-horizon/mandates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mandate_name: mandateName,
          description: mandateDesc,
          target_frequency: 'ON_EVALUATION',
          enforcement_level: 'MANDATORY_ALL_DEALS',
        }),
      });
      if (res.ok) {
        setMandateName('');
        setMandateDesc('');
        setShowMandateModal(false);
        await fetchSpace();
      }
    } catch (err) {
      console.error('Failed to create firm strategic mandate', err);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  const pendingActions = data?.pending_actions.filter((a) => a.status === 'PENDING_APPROVAL') || [];
  const resolvedActions = data?.pending_actions.filter((a) => a.status !== 'PENDING_APPROVAL') || [];

  return (
    <div className="space-y-6">
      {/* Top Banner & Philosophy */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl">⏱️</span>
              <h2 className="text-xl font-bold text-slate-100">
                Arca Autonomous Long-Horizon Deal Space
              </h2>
              <span className="bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border border-indigo-500/40 text-indigo-300 text-xs px-3 py-1 rounded-full font-bold">
                Agents Run the Diligence
              </span>
            </div>
            <p className="text-slate-400 text-sm mt-1 max-w-4xl">
              <strong className="text-slate-200">Autonomous vs. Copilot Paradigm:</strong> Diligence spans 30–60 days with many actors, handoffs, and external delays. Agents watch the world so people don't have to, maintain durable memory across weeks, and prompt the deal team with 1-click approvals after performing 90% of the groundwork.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start lg:self-center">
            <button
              onClick={() => setShowSignalModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-md transition-colors"
            >
              <span>⚡</span> Simulate World Signal
            </button>
            <button
              onClick={() => setShowConstraintModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold border border-slate-700 transition-colors"
            >
              <span>🧠</span> + Add Memory Rule
            </button>
          </div>
        </div>

        {/* 4 Core Primitives KPI Gauges */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6 pt-5 border-t border-slate-800">
          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Pending Partner Actions</div>
            <div className="text-3xl font-black text-amber-400 mt-1">
              {pendingActions.length}{' '}
              <span className="text-xs font-normal text-slate-500">Require 1-Click Sign-off</span>
            </div>
            <div className="text-xs text-emerald-400 font-medium mt-1">
              ✓ 90% of analytical groundwork complete
            </div>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">World Signals Evaluated</div>
            <div className="text-3xl font-black text-indigo-400 mt-1">
              {data?.signals_processed_count || 0}
            </div>
            <div className="text-xs text-slate-400 mt-1">Data room drops, founder emails, timer wakes</div>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Autonomous Watchers Registered</div>
            <div className="text-3xl font-black text-purple-400 mt-1">
              {data?.active_agents_count || 0}{' '}
              <span className="text-xs font-normal text-slate-400">Agents</span>
            </div>
            <div className="text-xs text-slate-400 mt-1">Watching external &amp; internal state</div>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Durable Constraints Active</div>
            <div className="text-3xl font-black text-emerald-400 mt-1">
              {data?.durable_constraints.length || 0}
            </div>
            <div className="text-xs text-slate-400 mt-1">Prohibited terms strictly respected</div>
          </div>
        </div>
      </div>

      {/* Horizon Navigation Sub-Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-950 p-1.5 rounded-xl border gap-2">
        <button
          onClick={() => setActiveTab('inbox')}
          className={`flex-1 py-2.5 px-4 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            activeTab === 'inbox'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <span>📥</span> Partner Action Queue ("Agents Prompt You")
          {pendingActions.length > 0 && (
            <span className="w-5 h-5 rounded-full bg-amber-500 text-slate-950 font-black text-[10px] flex items-center justify-center">
              {pendingActions.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('signals')}
          className={`flex-1 py-2.5 px-4 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            activeTab === 'signals'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <span>📡</span> Reactive Signal Stream ("Agents Watching the World")
        </button>

        <button
          onClick={() => setActiveTab('constraints')}
          className={`flex-1 py-2.5 px-4 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            activeTab === 'constraints'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <span>🧠</span> Durable Entity Memory (30-Day Constraints)
        </button>

        <button
          onClick={() => setActiveTab('mandates')}
          className={`flex-1 py-2.5 px-4 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            activeTab === 'mandates'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <span>🎯</span> Firm Strategic Mandates ("Steering the Firm")
        </button>
      </div>

      {/* TAB 1: Inverted Partner Action Inbox */}
      {activeTab === 'inbox' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span>Agents do 90% of the work in the background, preparing decisions for 1-click executive sign-off:</span>
            <span>{pendingActions.length} Actions Awaiting Review</span>
          </div>

          {pendingActions.length === 0 ? (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-500 text-sm">
              <span className="text-3xl block mb-2">🎉</span>
              All agent action proposals have been reviewed and resolved. Background watchers are actively monitoring signals.
            </div>
          ) : (
            pendingActions.map((action) => (
              <div
                key={action.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4 hover:border-slate-700 transition-all"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider border ${
                        action.priority === 'CRITICAL'
                          ? 'bg-rose-950 text-rose-300 border-rose-700'
                          : action.priority === 'HIGH'
                          ? 'bg-amber-950 text-amber-300 border-amber-700'
                          : 'bg-slate-800 text-slate-300 border-slate-700'
                      }`}
                    >
                      {action.priority} Priority
                    </span>
                    <span className="text-xs font-mono font-bold text-indigo-400">
                      🤖 Proposed by {action.agent_proposer}
                    </span>
                  </div>
                  <span className="text-xs text-slate-500 font-mono">
                    Created {new Date(action.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-bold text-slate-100">{action.headline}</h3>
                  <div className="bg-slate-950/80 p-3.5 rounded-lg border border-slate-800 mt-2 space-y-2">
                    <div className="text-xs text-slate-300">
                      <span className="font-semibold text-slate-400 block mb-1 uppercase tracking-wider text-[10px]">
                        Background Groundwork Performed by Agent:
                      </span>
                      {action.background_work_summary}
                    </div>

                    {action.precomputed_impact && Object.keys(action.precomputed_impact).length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800/80">
                        {Object.entries(action.precomputed_impact).map(([k, v]) => (
                          <span
                            key={k}
                            className="text-[11px] font-mono bg-indigo-950/60 text-indigo-300 px-2 py-0.5 rounded border border-indigo-800/60"
                          >
                            {k}: <strong className="text-white">{String(v)}</strong>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* 1-Click Action Buttons */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                  <div className="text-xs text-slate-500 italic">
                    Approving automatically registers an internal signal and updates the model.
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleResolveAction(action.id, false)}
                      disabled={actionProcessing === action.id}
                      className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition-colors border border-slate-700"
                    >
                      Reject Proposal
                    </button>
                    <button
                      onClick={() => handleResolveAction(action.id, true)}
                      disabled={actionProcessing === action.id}
                      className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg shadow-md transition-all flex items-center gap-2"
                    >
                      <span>✓</span>
                      {actionProcessing === action.id ? 'Executing...' : action.one_click_action_label}
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}

          {/* Resolved History */}
          {resolvedActions.length > 0 && (
            <div className="pt-6 space-y-3">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
                Resolved Action Audit Log ({resolvedActions.length})
              </h4>
              <div className="space-y-2">
                {resolvedActions.map((act) => (
                  <div
                    key={act.id}
                    className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs"
                  >
                    <div>
                      <span className="font-semibold text-slate-200">{act.headline}</span>
                      <span className="text-slate-500 block text-[11px]">
                        Resolved: {act.resolution_notes}
                      </span>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        act.status === 'APPROVED'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-rose-950 text-rose-400 border border-rose-800'
                      }`}
                    >
                      {act.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Reactive Signal Stream & Watchers */}
      {activeTab === 'signals' && (
        <div className="space-y-6">
          {/* Subscriptions Grid */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <span>👁️</span> Registered Autonomous Watchers ("Agents Registering Interest")
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {data?.subscriptions.map((sub) => (
                <div key={sub.id} className="p-3.5 bg-slate-950/70 rounded-xl border border-slate-800 space-y-1.5">
                  <div className="flex justify-between items-center">
                    <h4 className="font-bold text-indigo-300 text-xs">{sub.agent_name}</h4>
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  </div>
                  <p className="text-xs text-slate-400">
                    <span className="text-slate-300 font-medium">Condition: </span>
                    {sub.wake_condition}
                  </p>
                  <div className="flex justify-between text-[10px] font-mono text-slate-500 pt-1">
                    <span>Events: {sub.interested_signal_types.map((s) => s.split('_')[0]).join(', ')}</span>
                    <span>Woken: Just now</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Signals Stream Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <span>📡</span> Live Signal Journal (External Ingress &amp; Internal State Changes)
              </h3>
              <span className="text-xs text-slate-400">{data?.recent_signals.length} Events Logged</span>
            </div>
            <div className="divide-y divide-slate-800/80">
              {data?.recent_signals.map((sig) => (
                <div key={sig.id} className="p-4 hover:bg-slate-850 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                          sig.source === 'EXTERNAL_WORLD'
                            ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                            : sig.source === 'INTERNAL_UI'
                            ? 'bg-purple-950 text-purple-300 border border-purple-800'
                            : 'bg-amber-950 text-amber-300 border border-amber-800'
                        }`}
                      >
                        {sig.source.replace('_', ' ')}
                      </span>
                      <span className="text-xs font-semibold text-slate-300">{sig.title}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-slate-400">
                      <span>Acting Agents:</span>
                      {sig.acting_agents.map((ag) => (
                        <span key={ag} className="text-indigo-400 font-medium">
                          {ag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <span className="text-xs font-mono text-slate-500 self-start md:self-center">
                    {new Date(sig.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Durable Entity Memory */}
      {activeTab === 'constraints' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <span>🧠</span> Durable Entity Memory &amp; Prohibited Terms
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Persistent facts and rules collected over 30–60 days of interactions that all agents strictly enforce (e.g. "Never negotiate founder equity below 51%").
              </p>
            </div>
            <button
              onClick={() => setShowConstraintModal(true)}
              className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold"
            >
              + Add Rule
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            {data?.durable_constraints.map((c) => (
              <div key={c.id} className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                    {c.category}
                  </span>
                  <span className="text-[10px] text-emerald-400 font-bold">Active Invariant</span>
                </div>
                <h4 className="text-sm font-semibold text-slate-200">{c.rule_text}</h4>
                <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-800/80">
                  Source: <span className="text-slate-400">{c.source}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: Firm Strategic Mandates */}
      {activeTab === 'mandates' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <span>🎯</span> Firm-Wide Strategic Mandates ("Steering the Firm by Steering Agents")
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Managing Partners steer the firm by injecting top-level mandates that agents autonomously execute across all active diligences.
              </p>
            </div>
            <button
              onClick={() => setShowMandateModal(true)}
              className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold"
            >
              + Create Mandate
            </button>
          </div>

          <div className="space-y-3 pt-2">
            {data?.active_mandates.map((m) => (
              <div key={m.id} className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-1.5">
                <div className="flex justify-between items-center">
                  <h4 className="text-sm font-bold text-slate-100">{m.mandate_name}</h4>
                  <span className="text-[10px] font-mono px-2.5 py-0.5 rounded font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                    {m.enforcement_level}
                  </span>
                </div>
                <p className="text-xs text-slate-300">{m.description}</p>
                <div className="flex justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-800/80">
                  <span>Target Frequency: {m.target_frequency}</span>
                  <span>Enforced across {m.deals_enforced_count} portfolio diligences</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODAL: Simulate World Signal */}
      {showSignalModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-base font-bold text-slate-100">Simulate Inbound World Signal</h3>
              <button onClick={() => setShowSignalModal(false)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>
            <form onSubmit={handleSimulateSignal} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Signal Type</label>
                <select
                  value={sigType}
                  onChange={(e) => setSigType(e.target.value as SignalType)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none"
                >
                  <option value="FOUNDER_EMAIL_RECEIVED">Founder Email Received</option>
                  <option value="DATA_ROOM_FILE_DROPPED">Data Room File Dropped</option>
                  <option value="CUSTODIAN_SETTLEMENT_EVENT">Custodian Settlement Event</option>
                  <option value="MARKET_BENCHMARK_SHIFT">Market Benchmark Multiple Shift</option>
                  <option value="SCHEDULED_TIMER_WAKE">Scheduled Timer Wakeup</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Signal Headline / Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Elena (CEO) emailed updated Q3 NRR Cohorts"
                  value={sigTitle}
                  onChange={(e) => setSigTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Sender Email / Identifier</label>
                <input
                  type="text"
                  value={sigPayloadSender}
                  onChange={(e) => setSigPayloadSender(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowSignalModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 text-xs rounded-lg"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-indigo-600 text-white text-xs font-bold rounded-lg shadow-md">
                  Ingest &amp; Trigger Agents
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Add Durable Constraint */}
      {showConstraintModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-base font-bold text-slate-100">Add Durable Entity Memory Rule</h3>
              <button onClick={() => setShowConstraintModal(false)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>
            <form onSubmit={handleAddConstraint} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Category</label>
                <select
                  value={constraintCategory}
                  onChange={(e) => setConstraintCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none"
                >
                  <option value="EQUITY_STRUCTURE">Equity &amp; Cap Table</option>
                  <option value="VENDOR_RESTRICTION">Vendor &amp; Infrastructure</option>
                  <option value="KEY_PERSON_TERMS">Key Person &amp; Management</option>
                  <option value="TAX_LEGAL">Tax &amp; Legal Structure</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Rule / Invariant Text</label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Do not model liquidation preferences higher than 1x non-participating."
                  value={constraintRule}
                  onChange={(e) => setConstraintRule(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Fact Source</label>
                <input
                  type="text"
                  value={constraintSource}
                  onChange={(e) => setConstraintSource(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowConstraintModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 text-xs rounded-lg"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-indigo-600 text-white text-xs font-bold rounded-lg shadow-md">
                  Save Invariant
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Set Firm Strategic Mandate */}
      {showMandateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-base font-bold text-slate-100">Set Firm Strategic Mandate</h3>
              <button onClick={() => setShowMandateModal(false)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>
            <form onSubmit={handleAddMandate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Mandate Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Proactive AI Copyright & Training Data Indemnity Gate"
                  value={mandateName}
                  onChange={(e) => setMandateName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Description &amp; Rules</label>
                <textarea
                  required
                  rows={3}
                  placeholder="All targets training custom models must present third-party copyright indemnification."
                  value={mandateDesc}
                  onChange={(e) => setMandateDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowMandateModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 text-xs rounded-lg"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-indigo-600 text-white text-xs font-bold rounded-lg shadow-md">
                  Propagate Mandate to All Deals
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
