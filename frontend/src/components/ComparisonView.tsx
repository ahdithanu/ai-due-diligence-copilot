import React, { useState, useEffect } from 'react';
import { DealComparisonItem } from '../types';

export const ComparisonView: React.FC = () => {
  const [items, setItems] = useState<DealComparisonItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  const fetchComparisonData = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/investments/compare');
      if (res.ok) {
        const rawData = await res.json();
        const data: DealComparisonItem[] = Array.isArray(rawData) ? rawData : (rawData.companies || []);
        setItems(data);
        // Default select all investments for initial view
        setSelectedIds(new Set(data.map(item => item.investment_id)));
      }
    } catch (err) {
      console.error('Failed to fetch comparison data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparisonData();
  }, []);

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
  };

  const selectAll = () => {
    setSelectedIds(new Set(items.map(item => item.investment_id)));
  };

  const deselectAll = () => {
    setSelectedIds(new Set());
  };

  const selectedItems = items.filter(item => selectedIds.has(item.investment_id));

  const getRecommendationBadge = (rec?: string) => {
    const r = (rec || 'PENDING').toUpperCase();
    if (r === 'INVEST') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-700 shadow-sm shadow-emerald-900/50">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          INVEST
        </span>
      );
    }
    if (r === 'CONDITIONAL_PASS') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-950/80 text-amber-300 border border-amber-700 shadow-sm shadow-amber-900/50">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
          CONDITIONAL PASS
        </span>
      );
    }
    if (r === 'PASS') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-950/80 text-rose-300 border border-rose-700 shadow-sm shadow-rose-900/50">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
          PASS
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-300 border border-slate-700">
        PENDING
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Selector Bar */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-extrabold tracking-tight text-white flex items-center gap-2">
              <span>⚖️</span> Side-by-Side Deal Benchmarking
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Compare key financial metrics, IC recommendations, confidence scores, and dominant risk factors across prospective investments.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={selectAll}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold transition-all"
            >
              Select All ({items.length})
            </button>
            <button
              onClick={deselectAll}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 border border-slate-800 font-semibold transition-all"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Company Checkbox Selectors */}
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-800/80">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 mr-1">
            Pick Companies:
          </span>
          {items.map(item => {
            const isSelected = selectedIds.has(item.investment_id);
            return (
              <label
                key={item.investment_id}
                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-semibold cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-indigo-950/70 border-indigo-500 text-indigo-200 shadow-sm shadow-indigo-950'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300'
                }`}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleSelect(item.investment_id)}
                  className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-slate-900"
                />
                <span>{item.company_name}</span>
                <span className="text-[10px] opacity-75 font-mono">({item.target_round})</span>
              </label>
            );
          })}
        </div>
      </div>

      {/* Comparison Body */}
      {loading ? (
        <div className="glass-panel p-12 text-center text-slate-400 rounded-2xl">
          <div className="inline-block animate-spin w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full mb-3"></div>
          <p className="text-sm font-semibold">Loading deal comparison data...</p>
        </div>
      ) : selectedItems.length === 0 ? (
        <div className="glass-panel p-12 text-center rounded-2xl border border-dashed border-slate-800">
          <div className="text-3xl mb-2">🔍</div>
          <h3 className="text-base font-bold text-slate-200">No Investments Selected</h3>
          <p className="text-xs text-slate-400 mt-1 mb-4 max-w-md mx-auto">
            Select two or more companies above to generate a side-by-side deal evaluation matrix.
          </p>
          <button
            onClick={selectAll}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-600/30 transition-all"
          >
            Select All Deals
          </button>
        </div>
      ) : (
        <div className="glass-panel rounded-2xl border border-slate-800 overflow-x-auto shadow-2xl">
          <table className="w-full text-left border-collapse min-w-[700px]">
            <thead>
              <tr className="bg-slate-950/80 border-b border-slate-800">
                <th className="p-4 w-56 text-xs font-extrabold uppercase tracking-wider text-slate-400 sticky left-0 bg-slate-950 z-10 border-r border-slate-800">
                  Deal Comparison Metric
                </th>
                {selectedItems.map(item => (
                  <th key={item.investment_id} className="p-4 text-slate-100 min-w-[220px]">
                    <div className="font-extrabold text-sm text-white">{item.company_name}</div>
                    <div className="text-xs text-indigo-400 font-mono mt-0.5">{item.industry}</div>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {item.target_round}
                      </span>
                      {item.check_size_usd && (
                        <span className="text-xs font-semibold text-emerald-400 font-mono">
                          ${(item.check_size_usd / 1000000).toFixed(1)}M Check
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs">
              {/* Recommendation Row */}
              <tr className="hover:bg-slate-900/40 transition-colors">
                <td className="p-4 font-bold text-slate-300 sticky left-0 bg-[#090d16] z-10 border-r border-slate-800">
                  IC Recommendation
                </td>
                {selectedItems.map(item => (
                  <td key={item.investment_id} className="p-4">
                    {getRecommendationBadge(item.recommendation)}
                  </td>
                ))}
              </tr>

              {/* Confidence Score Row */}
              <tr className="hover:bg-slate-900/40 transition-colors">
                <td className="p-4 font-bold text-slate-300 sticky left-0 bg-[#090d16] z-10 border-r border-slate-800">
                  Confidence Score
                </td>
                {selectedItems.map(item => {
                  const scorePct = Math.round((item.confidence_score || 0) * 100);
                  return (
                    <td key={item.investment_id} className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="flex-1 bg-slate-800 h-2 rounded-full overflow-hidden border border-slate-700">
                          <div
                            className="bg-gradient-to-r from-indigo-500 to-cyan-400 h-full rounded-full transition-all duration-500"
                            style={{ width: `${scorePct}%` }}
                          ></div>
                        </div>
                        <span className="font-mono font-bold text-slate-200">{scorePct}%</span>
                      </div>
                    </td>
                  );
                })}
              </tr>

              {/* Section Divider: Financial Metrics */}
              <tr className="bg-indigo-950/30 border-t border-b border-indigo-900/50">
                <td colSpan={selectedItems.length + 1} className="p-2.5 px-4 font-extrabold uppercase tracking-widest text-[11px] text-indigo-300">
                  📊 Financial & Unit Economic Benchmarks
                </td>
              </tr>

              {/* ARR */}
              <tr className="hover:bg-slate-900/40 transition-colors">
                <td className="p-4 font-semibold text-slate-400 sticky left-0 bg-[#090d16] z-10 border-r border-slate-800">
                  ARR / Revenue
                </td>
                {selectedItems.map(item => (
                  <td key={item.investment_id} className="p-4 font-mono font-bold text-emerald-400 text-sm">
                    {item.key_metrics.arr}
                  </td>
                ))}
              </tr>

              {/* Gross Margin */}
              <tr className="hover:bg-slate-900/40 transition-colors">
                <td className="p-4 font-semibold text-slate-400 sticky left-0 bg-[#090d16] z-10 border-r border-slate-800">
                  Gross Margin
                </td>
                {selectedItems.map(item => (
                  <td key={item.investment_id} className="p-4 font-mono font-bold text-slate-200">
                    {item.key_metrics.gross_margin}
                  </td>
                ))}
              </tr>

              {/* NRR */}
              <tr className="hover:bg-slate-900/40 transition-colors">
                <td className="p-4 font-semibold text-slate-400 sticky left-0 bg-[#090d16] z-10 border-r border-slate-800">
                  Net Revenue Retention (NRR)
                </td>
                {selectedItems.map(item => (
                  <td key={item.investment_id} className="p-4 font-mono font-bold text-cyan-300">
                    {item.key_metrics.nrr}
                  </td>
                ))}
              </tr>

              {/* LTV / CAC */}
              <tr className="hover:bg-slate-900/40 transition-colors">
                <td className="p-4 font-semibold text-slate-400 sticky left-0 bg-[#090d16] z-10 border-r border-slate-800">
                  LTV / CAC Ratio
                </td>
                {selectedItems.map(item => (
                  <td key={item.investment_id} className="p-4 font-mono font-bold text-indigo-300">
                    {item.key_metrics.ltv_cac}
                  </td>
                ))}
              </tr>

              {/* Runway */}
              <tr className="hover:bg-slate-900/40 transition-colors">
                <td className="p-4 font-semibold text-slate-400 sticky left-0 bg-[#090d16] z-10 border-r border-slate-800">
                  Implied Runway
                </td>
                {selectedItems.map(item => (
                  <td key={item.investment_id} className="p-4 font-mono font-bold text-slate-200">
                    {item.key_metrics.runway}
                  </td>
                ))}
              </tr>

              {/* Section Divider: Risk Factors */}
              <tr className="bg-rose-950/30 border-t border-b border-rose-900/50">
                <td colSpan={selectedItems.length + 1} className="p-2.5 px-4 font-extrabold uppercase tracking-widest text-[11px] text-rose-300">
                  ⚠️ Dominant Deal Risks & Vulnerabilities
                </td>
              </tr>

              {/* Dominant Risks List */}
              <tr className="hover:bg-slate-900/40 transition-colors">
                <td className="p-4 font-bold text-slate-300 sticky left-0 bg-[#090d16] z-10 border-r border-slate-800 align-top">
                  Key Red Flags & Concerns
                </td>
                {selectedItems.map(item => (
                  <td key={item.investment_id} className="p-4 align-top">
                    {item.dominant_risks.length > 0 ? (
                      <ul className="space-y-2">
                        {item.dominant_risks.map((risk, i) => (
                          <li key={i} className="flex items-start gap-2 text-slate-300 text-xs">
                            <span className="text-rose-400 mt-0.5">•</span>
                            <span>{risk}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className="text-slate-500 italic">No critical risks flagged</span>
                    )}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
