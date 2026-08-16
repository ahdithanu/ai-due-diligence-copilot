import React, { useState, useEffect } from 'react';
import { RedFlagAlert, MaterialityLevel } from '../types';

export const RiskRadarView: React.FC = () => {
  const [alerts, setAlerts] = useState<RedFlagAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<'ALL' | 'CRITICAL' | 'HIGH' | 'MEDIUM'>('ALL');
  const [companyFilter, setCompanyFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchRedFlags = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/investments/red-flags');
      if (res.ok) {
        const data: RedFlagAlert[] = await res.json();
        setAlerts(data);
      }
    } catch (err) {
      console.error('Failed to fetch red flag alerts', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRedFlags();
  }, []);

  // Unique list of companies from alerts
  const companyNames = Array.from(new Set(alerts.map(a => a.company_name)));

  // Filtered alerts
  const filteredAlerts = alerts.filter(alert => {
    const matchesSev = severityFilter === 'ALL' || alert.severity === severityFilter;
    const matchesComp = companyFilter === 'ALL' || alert.company_name === companyFilter;
    const matchesSearch =
      searchQuery === '' ||
      alert.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alert.evidence_citation.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alert.mitigation_action.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSev && matchesComp && matchesSearch;
  });

  const criticalCount = alerts.filter(a => a.severity === 'CRITICAL').length;
  const highCount = alerts.filter(a => a.severity === 'HIGH').length;
  const mediumCount = alerts.filter(a => a.severity === 'MEDIUM').length;

  const getSeverityBadge = (sev: MaterialityLevel) => {
    switch (sev) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-rose-950 text-rose-200 border border-rose-600 shadow-md shadow-rose-900/50">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
            CRITICAL DEAL-KILLER
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-950 text-amber-200 border border-amber-600 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-amber-400"></span>
            HIGH RISK
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-950 text-blue-200 border border-blue-600">
            <span className="w-2 h-2 rounded-full bg-blue-400"></span>
            MEDIUM ALERT
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-300 border border-slate-700">
            LOW
          </span>
        );
    }
  };

  const renderAlertCard = (alert: RedFlagAlert) => {
    let borderClass = 'border-l-4 border-slate-700 bg-slate-900/40';
    if (alert.severity === 'CRITICAL') {
      borderClass = 'border-l-4 border-rose-500 bg-rose-950/20 hover:bg-rose-950/30';
    } else if (alert.severity === 'HIGH') {
      borderClass = 'border-l-4 border-amber-500 bg-amber-950/20 hover:bg-amber-950/30';
    } else if (alert.severity === 'MEDIUM') {
      borderClass = 'border-l-4 border-blue-500 bg-blue-950/20 hover:bg-blue-950/30';
    }

    return (
      <div
        key={alert.id}
        className={`glass-panel p-6 rounded-2xl border border-slate-800/80 transition-all duration-200 ${borderClass} space-y-4 shadow-lg`}
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {getSeverityBadge(alert.severity)}
            <span className="px-2.5 py-0.5 rounded-lg text-xs font-mono font-bold bg-slate-950 text-slate-300 border border-slate-800">
              🏢 {alert.company_name}
            </span>
            <span className="px-2.5 py-0.5 rounded-lg text-[11px] font-semibold bg-indigo-950/80 text-indigo-300 border border-indigo-800">
              {alert.category}
            </span>
          </div>
        </div>

        <div>
          <h3 className="text-base font-extrabold text-white tracking-tight">{alert.title}</h3>
        </div>

        {/* Evidence Citation */}
        <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800/80 space-y-1.5">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <span>📖</span> Primary Evidence Citation
          </div>
          <p className="text-xs text-slate-300 italic font-serif leading-relaxed pl-3 border-l-2 border-slate-700">
            "{alert.evidence_citation}"
          </p>
        </div>

        {/* Recommended Mitigation Action */}
        <div className="bg-emerald-950/30 rounded-xl p-4 border border-emerald-800/50 space-y-1.5">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-300 flex items-center gap-1.5">
            <span>🛡️</span> Recommended IC Mitigation Action
          </div>
          <p className="text-xs text-emerald-200 font-medium leading-relaxed">
            {alert.mitigation_action}
          </p>
        </div>
      </div>
    );
  };

  const groupedSeverities: Array<'CRITICAL' | 'HIGH' | 'MEDIUM'> = ['CRITICAL', 'HIGH', 'MEDIUM'];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold tracking-tight text-white flex items-center gap-2">
            <span>🚨</span> Risk Radar & Deal-Killer Alert Dashboard
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time monitoring of critical vulnerabilities, customer concentration, key-person risks, and material contradictions across prospective deals.
          </p>
        </div>
      </div>

      {/* Summary KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Flagged Alerts</div>
          <div className="text-2xl font-black text-white mt-1">{alerts.length}</div>
          <div className="text-[11px] text-slate-500 mt-1">Across all pipeline deals</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-rose-900/60 bg-rose-950/20">
          <div className="text-xs font-bold uppercase tracking-wider text-rose-300 flex items-center justify-between">
            <span>Critical Deal-Killers</span>
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
          </div>
          <div className="text-2xl font-black text-rose-200 mt-1">{criticalCount}</div>
          <div className="text-[11px] text-rose-400/80 mt-1">Requires immediate IC gating</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-amber-900/60 bg-amber-950/20">
          <div className="text-xs font-bold uppercase tracking-wider text-amber-300">High Severity Risks</div>
          <div className="text-2xl font-black text-amber-200 mt-1">{highCount}</div>
          <div className="text-[11px] text-amber-400/80 mt-1">Actionable mitigation needed</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-blue-900/60 bg-blue-950/20">
          <div className="text-xs font-bold uppercase tracking-wider text-blue-300">Medium Alerts</div>
          <div className="text-2xl font-black text-blue-200 mt-1">{mediumCount}</div>
          <div className="text-[11px] text-blue-400/80 mt-1">Monitor during diligence</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col md:flex-row items-center gap-4 justify-between">
        {/* Severity Tabs */}
        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800 w-full md:w-auto">
          {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'] as const).map(sev => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                severityFilter === sev
                  ? sev === 'CRITICAL'
                    ? 'bg-rose-600 text-white'
                    : sev === 'HIGH'
                    ? 'bg-amber-600 text-white'
                    : sev === 'MEDIUM'
                    ? 'bg-blue-600 text-white'
                    : 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        {/* Company Dropdown & Search */}
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
          <select
            value={companyFilter}
            onChange={e => setCompanyFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs font-semibold rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 w-full sm:w-auto"
          >
            <option value="ALL">All Companies ({companyNames.length})</option>
            {companyNames.map(name => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>

          <input
            type="text"
            placeholder="Search alerts or evidence..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs rounded-xl px-3 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-full sm:w-64"
          />
        </div>
      </div>

      {/* Main Alert List Grouped by Severity */}
      {loading ? (
        <div className="glass-panel p-12 text-center text-slate-400 rounded-2xl">
          <div className="inline-block animate-spin w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full mb-3"></div>
          <p className="text-sm font-semibold">Scanning portfolio risks & evidence citations...</p>
        </div>
      ) : filteredAlerts.length === 0 ? (
        <div className="glass-panel p-12 text-center rounded-2xl border border-dashed border-slate-800">
          <div className="text-3xl mb-2">🛡️</div>
          <h3 className="text-base font-bold text-slate-200">No Risk Alerts Found</h3>
          <p className="text-xs text-slate-400 mt-1">
            No red flag alerts matched your current search filters.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {groupedSeverities.map(sev => {
            const groupAlerts = filteredAlerts.filter(a => a.severity === sev);
            if (groupAlerts.length === 0) return null;

            return (
              <div key={sev} className="space-y-4">
                <div className="flex items-center gap-3 border-b border-slate-800 pb-2">
                  <h3 className="text-sm font-black uppercase tracking-wider text-slate-300 flex items-center gap-2">
                    {sev === 'CRITICAL' && <span className="text-rose-500">🚨</span>}
                    {sev === 'HIGH' && <span className="text-amber-500">⚠️</span>}
                    {sev === 'MEDIUM' && <span className="text-blue-500">⚡</span>}
                    {sev} Severity Red Flags ({groupAlerts.length})
                  </h3>
                </div>

                <div className="grid grid-cols-1 gap-4">
                  {groupAlerts.map(renderAlertCard)}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
