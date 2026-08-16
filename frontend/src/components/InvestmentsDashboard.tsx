import React, { useState } from 'react';
import { InvestmentSummary, DiligenceStatus, DeploymentConfig } from '../types';

interface DashboardProps {
  investments: InvestmentSummary[];
  deployments?: DeploymentConfig[];
  loading: boolean;
  onSelectInvestment: (id: string) => void;
  onCreateInvestment: (data: { company_name: string; industry: string; target_round: string; check_size_usd?: number; deployment_id?: string }) => Promise<void>;
  onRefresh: () => void;
}

export const InvestmentsDashboard: React.FC<DashboardProps> = ({
  investments,
  deployments = [],
  loading,
  onSelectInvestment,
  onCreateInvestment,
  onRefresh
}) => {
  const [showModal, setShowModal] = useState(false);
  const [companyName, setCompanyName] = useState('');
  const [industry, setIndustry] = useState('');
  const [targetRound, setTargetRound] = useState('Series A');
  const [checkSize, setCheckSize] = useState<string>('5000000');
  const [deploymentId, setDeploymentId] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyName || !industry) return;
    setSubmitting(true);
    try {
      await onCreateInvestment({
        company_name: companyName,
        industry,
        target_round: targetRound,
        check_size_usd: checkSize ? parseFloat(checkSize) : undefined,
        deployment_id: deploymentId || (deployments[0]?.deployment_id || undefined)
      });
      setShowModal(false);
      setCompanyName('');
      setIndustry('');
      setCheckSize('5000000');
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: DiligenceStatus) => {
    switch (status) {
      case 'HUMAN_REVIEW':
        return <span className="badge-status badge-review">⚠️ Human Review Gate</span>;
      case 'COMPLETED':
      case 'MEMO_GENERATED':
        return <span className="badge-status badge-invest">✓ Completed</span>;
      case 'FAILED':
        return <span className="badge-status badge-pass">✕ Failed / Rejected</span>;
      default:
        return <span className="badge-status badge-conditional">🔄 {status.replace('_', ' ')}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-6 rounded-2xl border border-indigo-500/20">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/30 border border-indigo-400/40 flex items-center justify-center text-indigo-400 font-bold text-lg">
              AI
            </div>
            <div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">Investment Workspaces</h1>
              <p className="text-sm text-slate-400">Autonomous Multi-Agent Due Diligence Copilot</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            className="px-4 py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 text-sm font-medium transition-all"
          >
            ↻ Refresh Workspaces
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition-all transform hover:-translate-y-0.5"
          >
            + Create New Workspace
          </button>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-xl border border-slate-800">
          <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Total Deals</div>
          <div className="text-3xl font-extrabold text-white mt-1">{investments.length}</div>
        </div>
        <div className="glass-panel p-5 rounded-xl border border-slate-800">
          <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Human Review Paused</div>
          <div className="text-3xl font-extrabold text-rose-400 mt-1">
            {investments.filter(i => i.status === 'HUMAN_REVIEW').length}
          </div>
        </div>
        <div className="glass-panel p-5 rounded-xl border border-slate-800">
          <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Completed Diligence</div>
          <div className="text-3xl font-extrabold text-emerald-400 mt-1">
            {investments.filter(i => i.status === 'COMPLETED' || i.status === 'MEMO_GENERATED').length}
          </div>
        </div>
        <div className="glass-panel p-5 rounded-xl border border-slate-800">
          <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold">In Progress</div>
          <div className="text-3xl font-extrabold text-indigo-400 mt-1">
            {investments.filter(i => i.status !== 'COMPLETED' && i.status !== 'MEMO_GENERATED' && i.status !== 'HUMAN_REVIEW' && i.status !== 'FAILED').length}
          </div>
        </div>
      </div>

      {/* Deal Cards List */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-200">Active Investment Workspaces</h2>

        {loading ? (
          <div className="glass-panel p-12 text-center text-slate-400 rounded-2xl">
            <div className="inline-block animate-spin w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full mb-3"></div>
            <p>Loading investment workspaces...</p>
          </div>
        ) : investments.length === 0 ? (
          <div className="glass-panel p-12 text-center text-slate-400 rounded-2xl border border-dashed border-slate-800">
            <p className="text-base text-slate-300 font-medium">No investment workspaces created yet.</p>
            <p className="text-sm text-slate-500 mt-1">Click "+ Create New Workspace" to initiate autonomous diligence.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {investments.map(inv => (
              <div
                key={inv.investment_id}
                onClick={() => onSelectInvestment(inv.investment_id)}
                className="glass-card p-6 rounded-2xl cursor-pointer flex flex-col justify-between group hover:border-indigo-500/50"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <h3 className="text-xl font-bold text-white group-hover:text-indigo-400 transition-colors">
                      {inv.company_name}
                    </h3>
                    {getStatusBadge(inv.status)}
                  </div>
                  
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 mb-4">
                    <span className="px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300">
                      {inv.industry}
                    </span>
                    <span className="px-2.5 py-1 rounded-md bg-indigo-950/60 border border-indigo-800/50 text-indigo-300">
                      {inv.target_round}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs bg-slate-900/60 p-3 rounded-xl border border-slate-800/80 mb-4">
                    <div>
                      <span className="text-slate-500 block">Target Check:</span>
                      <span className="font-mono font-semibold text-slate-200">
                        {inv.check_size_usd ? `$${(inv.check_size_usd / 1000000).toFixed(2)}M` : 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Evidence Count:</span>
                      <span className="font-mono font-semibold text-slate-200">{inv.evidence_count} records</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs text-slate-400">
                  <span>Created {new Date(inv.created_at).toLocaleDateString()}</span>
                  <span className="font-medium text-indigo-400 group-hover:translate-x-1 transition-transform inline-flex items-center gap-1">
                    Open Workspace &rarr;
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal for Creating Workspace */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="glass-panel w-full max-w-md p-6 rounded-2xl border border-indigo-500/30 shadow-2xl space-y-5">
            <div className="flex justify-between items-center pb-3 border-b border-slate-800">
              <h3 className="text-lg font-bold text-white">Create Diligence Workspace</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Company Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Robotics Inc."
                  value={companyName}
                  onChange={e => setCompanyName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Industry / Sector</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Enterprise SaaS / AI Infrastructure"
                  value={industry}
                  onChange={e => setIndustry(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Customer Deployment Profile</label>
                <select
                  value={deploymentId}
                  onChange={e => setDeploymentId(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Default Profile</option>
                  {deployments.map(dep => (
                    <option key={dep.deployment_id} value={dep.deployment_id}>
                      {dep.investment_strategy === 'growth_equity_saas' ? 'Growth Equity SaaS' : 'Traditional Buyout'} - {dep.customer_name} ({dep.deployment_name})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Target Round</label>
                  <select
                    value={targetRound}
                    onChange={e => setTargetRound(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Pre-Seed">Pre-Seed</option>
                    <option value="Seed">Seed</option>
                    <option value="Series A">Series A</option>
                    <option value="Series B">Series B</option>
                    <option value="Series C+">Series C+</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Check Size (USD)</label>
                  <input
                    type="number"
                    value={checkSize}
                    onChange={e => setCheckSize(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-md"
                >
                  {submitting ? 'Creating...' : 'Initialize Workspace'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
