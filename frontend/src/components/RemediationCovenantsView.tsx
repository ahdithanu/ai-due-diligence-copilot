import React, { useState, useEffect } from 'react';
import {
  RemediationPlanResponse,
  ConditionPrecedentStatus,
} from '../types';

interface RemediationCovenantsViewProps {
  investmentId: string;
  companyName?: string;
  valuation?: number;
}

export const RemediationCovenantsView: React.FC<RemediationCovenantsViewProps> = ({
  investmentId,
  companyName = 'Acme SaaS AI',
  valuation = 50000000,
}) => {
  const [data, setData] = useState<RemediationPlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeDayRange, setActiveDayRange] = useState<'DAYS_1_30' | 'DAYS_31_60' | 'DAYS_61_100'>('DAYS_1_30');
  const [showAddMilestone, setShowAddMilestone] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newWorkstream, setNewWorkstream] = useState('GTM_EXPANSION');
  const [newImpact, setNewImpact] = useState('');
  const [newOwner, setNewOwner] = useState('Operating Partner');

  const fetchPlan = async () => {
    setLoading(true);
    try {
      const url = `/api/v1/investments/${investmentId}/remediation-plan?company_name=${encodeURIComponent(
        companyName
      )}&valuation=${valuation}`;
      const res = await fetch(url);
      if (res.ok) {
        const json: RemediationPlanResponse = await res.json();
        setData(json);
      }
    } catch (err) {
      console.error('Failed to load remediation plan', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlan();
  }, [investmentId, companyName, valuation]);

  const handleToggleCPStatus = async (cpId: string, currentStatus: ConditionPrecedentStatus) => {
    const nextStatus: ConditionPrecedentStatus =
      currentStatus === 'PENDING_TARGET_ACTION'
        ? 'SATISFIED'
        : currentStatus === 'SATISFIED'
        ? 'WAIVED'
        : 'PENDING_TARGET_ACTION';

    try {
      const res = await fetch(
        `/api/v1/investments/${investmentId}/remediation-plan/conditions/${cpId}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: nextStatus }),
        }
      );
      if (res.ok) {
        await fetchPlan();
      }
    } catch (err) {
      console.error('Failed to update condition precedent', err);
    }
  };

  const handleCreateMilestone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      const res = await fetch(
        `/api/v1/investments/${investmentId}/remediation-plan/milestones`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            day_range: activeDayRange,
            workstream: newWorkstream,
            milestone_title: newTitle,
            target_kpi_impact: newImpact || 'Operational efficiency improvement',
            owner: newOwner,
          }),
        }
      );
      if (res.ok) {
        setNewTitle('');
        setNewImpact('');
        setShowAddMilestone(false);
        await fetchPlan();
      }
    } catch (err) {
      console.error('Failed to create milestone', err);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  const satisfiedCount =
    data?.conditions_precedent.filter((c) => c.status === 'SATISFIED').length || 0;
  const totalCPs = data?.conditions_precedent.length || 0;

  const filteredMilestones =
    data?.value_creation_plan.filter((m) => m.day_range === activeDayRange) || [];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl">🛡️</span>
              <h2 className="text-xl font-bold text-slate-100">
                Red-Flag Remediation, Covenants &amp; 100-Day Value Creation Plan
              </h2>
              <span className="bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs px-2.5 py-1 rounded-full font-semibold">
                Definitive SPA Terms
              </span>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Translates diligence red flags into binding closing conditions, indemnity escrow holdbacks, protective board covenants, and a post-close 100-day operational roadmap.
            </p>
          </div>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-5 border-t border-slate-800">
          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Conditions Precedent (Closing CPs)</div>
            <div className="text-3xl font-black text-emerald-400 mt-1">
              {satisfiedCount} <span className="text-base font-normal text-slate-500">/ {totalCPs} Satisfied</span>
            </div>
            <div className="text-xs text-slate-500 mt-1">Click badge in table to toggle status</div>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Total Indemnity Escrow Holdback</div>
            <div className="text-3xl font-black text-amber-400 mt-1">
              ${((data?.total_escrow_holdback_usd || 0) / 1000000).toFixed(1)}M
            </div>
            <div className="text-xs text-slate-400 mt-1">
              10.0% of purchase price (12–18 mo survival)
            </div>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">100-Day Value Milestones</div>
            <div className="text-3xl font-black text-indigo-400 mt-1">
              {data?.value_creation_plan.length || 0}
            </div>
            <div className="text-xs text-slate-400 mt-1">Active across 3 operating horizons</div>
          </div>
        </div>
      </div>

      {/* Section 1: Closing Conditions Precedent (CPs) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>⚖️</span> Pre-Closing Conditions Precedent (Definitive Agreement Obligations)
          </h3>
          <span className="text-xs text-slate-400">Target company must satisfy before capital transfer</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950 text-xs uppercase text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Category</th>
                <th className="p-3">Condition Precedent (CP) Obligation</th>
                <th className="p-3">Risk Mitigated</th>
                <th className="p-3">Responsible</th>
                <th className="p-3 text-right">Status (Click to toggle)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {data?.conditions_precedent.map((cp) => (
                <tr key={cp.id} className="hover:bg-slate-850 transition-colors">
                  <td className="p-3 font-mono text-xs font-bold text-indigo-400">{cp.category}</td>
                  <td className="p-3 font-medium text-slate-200">{cp.condition_text}</td>
                  <td className="p-3 text-xs text-slate-400">{cp.risk_mitigated}</td>
                  <td className="p-3 text-xs text-slate-300">{cp.responsible_party}</td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => handleToggleCPStatus(cp.id, cp.status)}
                      className={`text-xs px-3 py-1 rounded-full font-bold transition-all border ${
                        cp.status === 'SATISFIED'
                          ? 'bg-emerald-950 text-emerald-300 border-emerald-600 hover:bg-emerald-900'
                          : cp.status === 'PENDING_TARGET_ACTION'
                          ? 'bg-amber-950 text-amber-300 border-amber-600 hover:bg-amber-900'
                          : 'bg-slate-800 text-slate-300 border-slate-600 hover:bg-slate-700'
                      }`}
                    >
                      {cp.status === 'PENDING_TARGET_ACTION' ? '⏳ PENDING ACTION' : cp.status}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 2 & 3: Escrows & Governance Covenants */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Escrow Holdbacks */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>🔒</span> Special Indemnity &amp; Escrow Holdbacks
          </h3>
          <div className="space-y-3">
            {data?.escrows.map((e) => (
              <div key={e.id} className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-2">
                <div className="flex justify-between items-start">
                  <h4 className="font-semibold text-slate-200 text-sm">{e.title}</h4>
                  <span className="font-mono text-emerald-400 font-bold text-sm">
                    ${(e.holdback_amount_usd / 1000000).toFixed(1)}M ({e.holdback_pct}%)
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  <span className="text-slate-300 font-medium">Trigger Event: </span>
                  {e.trigger_event}
                </p>
                <div className="flex justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-800/80">
                  <span>Survival: {e.survival_period_months} Months</span>
                  <span>{e.release_conditions}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Governance & Negative Covenants */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>📜</span> Board Governance &amp; Negative Covenants
          </h3>
          <div className="space-y-3">
            {data?.covenants.map((cov) => (
              <div key={cov.id} className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-1.5">
                <div className="flex justify-between items-center">
                  <h4 className="font-semibold text-slate-200 text-sm">{cov.clause_title}</h4>
                  <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                    {cov.covenant_type}
                  </span>
                </div>
                <p className="text-xs text-slate-400">{cov.description}</p>
                {cov.threshold_usd && (
                  <div className="text-[11px] font-mono text-amber-400 pt-1">
                    Threshold: ${cov.threshold_usd.toLocaleString()}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Section 4: 100-Day Value Creation Roadmap */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <span>🚀</span> Post-Close 100-Day Operational Value Creation Roadmap
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Phased strategic roadmap implemented by operating partners to drive EBITDA expansion and churn suppression.
            </p>
          </div>
          <button
            onClick={() => setShowAddMilestone(true)}
            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-md"
          >
            + Add Milestone
          </button>
        </div>

        {/* Horizon Tabs */}
        <div className="flex border-b border-slate-800 gap-2">
          {[
            { id: 'DAYS_1_30', label: 'Days 1 - 30 (Immediate Control & Governance)' },
            { id: 'DAYS_31_60', label: 'Days 31 - 60 (GTM & Margin Expansion)' },
            { id: 'DAYS_61_100', label: 'Days 61 - 100 (Scale & Enterprise Readiness)' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveDayRange(tab.id as any)}
              className={`pb-3 px-3 text-xs font-bold transition-all border-b-2 ${
                activeDayRange === tab.id
                  ? 'border-indigo-500 text-white'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Milestones Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredMilestones.map((m) => (
            <div
              key={m.id}
              className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-2 hover:border-slate-700 transition-all"
            >
              <div className="flex justify-between items-start">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-indigo-950/80 text-indigo-300 border border-indigo-800">
                  {m.workstream.replace('_', ' ')}
                </span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    m.status === 'ACHIEVED'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                      : m.status === 'IN_PROGRESS'
                      ? 'bg-amber-950 text-amber-300 border border-amber-800'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {m.status}
                </span>
              </div>
              <h4 className="font-semibold text-slate-200 text-sm">{m.milestone_title}</h4>
              <p className="text-xs text-slate-300 bg-slate-900/80 p-2.5 rounded-lg border border-slate-800/80">
                <span className="font-semibold text-indigo-400">Target KPI Impact: </span>
                {m.target_kpi_impact}
              </p>
              <div className="text-[11px] text-slate-500 pt-1">
                Owner: <span className="text-slate-300 font-medium">{m.owner}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Add Milestone Modal */}
      {showAddMilestone && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-base font-bold text-slate-100">Add 100-Day Value Milestone</h3>
              <button onClick={() => setShowAddMilestone(false)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>
            <form onSubmit={handleCreateMilestone} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Milestone Action</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Audit Sales Compensation Quota Plans"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Workstream</label>
                <select
                  value={newWorkstream}
                  onChange={(e) => setNewWorkstream(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none"
                >
                  <option value="FINANCE_OPS">Finance &amp; Operations</option>
                  <option value="GTM_EXPANSION">GTM &amp; Sales Capacity</option>
                  <option value="TECH_ARCH">Technical &amp; Cloud Arch</option>
                  <option value="TALENT_HR">Talent &amp; Executive HR</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Target KPI Impact</label>
                <input
                  type="text"
                  placeholder="e.g. Expand pipeline by $4.5M ARR"
                  value={newImpact}
                  onChange={(e) => setNewImpact(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Responsible Owner</label>
                <input
                  type="text"
                  value={newOwner}
                  onChange={(e) => setNewOwner(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddMilestone(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 text-xs rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg"
                >
                  Save Milestone
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
