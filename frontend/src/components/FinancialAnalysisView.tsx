import React, { useState } from 'react';
import { FinancialMetricRecord } from '../types';

interface FinancialAnalysisViewProps {
  metrics: FinancialMetricRecord[];
}

export const FinancialAnalysisView: React.FC<FinancialAnalysisViewProps> = ({ metrics }) => {
  const [selectedMetric, setSelectedMetric] = useState<FinancialMetricRecord | null>(null);

  const formatValue = (m: FinancialMetricRecord) => {
    if (m.unit === 'USD') return `$${m.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (m.unit === 'percentage' || m.unit === '%') return `${m.value.toFixed(1)}%`;
    if (m.unit === 'months') return `${m.value.toFixed(1)} mos`;
    return `${m.value}`;
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-indigo-500/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>📊 Deterministic Financial Analysis Engine</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">
              Math Verified
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Exact mathematical formulas calculated from grounded evidence records without LLM hallucination.
          </p>
        </div>
      </div>

      {/* Financial Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        {metrics.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            No financial metrics calculated yet. Upload financial statements or operating metrics documents to trigger extraction.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 font-mono uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-5 py-4">Metric Name</th>
                  <th className="px-5 py-4">Value</th>
                  <th className="px-5 py-4">Period</th>
                  <th className="px-5 py-4">Formula</th>
                  <th className="px-5 py-4">Confidence</th>
                  <th className="px-5 py-4 text-right">Evidence Links</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {metrics.map((m, idx) => (
                  <tr
                    key={m.id || idx}
                    onClick={() => setSelectedMetric(m)}
                    className="hover:bg-slate-900/60 transition-colors cursor-pointer"
                  >
                    <td className="px-5 py-4 font-bold text-slate-100 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                      {m.metric_name}
                    </td>
                    <td className="px-5 py-4 text-sm font-extrabold text-indigo-300">
                      {formatValue(m)}
                    </td>
                    <td className="px-5 py-4 text-slate-300">{m.period}</td>
                    <td className="px-5 py-4 text-slate-400 max-w-xs truncate">{m.formula}</td>
                    <td className="px-5 py-4">
                      <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[11px]">
                        {(m.confidence * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right font-sans">
                      <span className="text-indigo-400 font-bold hover:underline">
                        {m.input_evidence_ids.length} citations &rarr;
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Selected Metric Audit Modal / Drawer */}
      {selectedMetric && (
        <div className="glass-panel p-6 rounded-2xl border border-indigo-500/40 space-y-4">
          <div className="flex justify-between items-center pb-2 border-b border-slate-800">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>Formula Audit:</span>
              <span className="text-indigo-400 font-mono">{selectedMetric.metric_name}</span>
            </h3>
            <button onClick={() => setSelectedMetric(null)} className="text-slate-400 hover:text-white text-sm">✕ Close</button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-slate-500 block">Calculated Value:</span>
              <span className="text-xl font-bold text-emerald-400 mt-1 block">{formatValue(selectedMetric)}</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-slate-500 block">Period:</span>
              <span className="text-sm font-semibold text-slate-200 mt-1 block">{selectedMetric.period}</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-slate-500 block">Engine Type:</span>
              <span className="text-sm font-semibold text-indigo-300 mt-1 block">Deterministic Python Calculator</span>
            </div>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1 text-xs">
            <span className="text-slate-500 font-mono font-bold block uppercase">Mathematical Formula:</span>
            <code className="text-indigo-300 font-mono block bg-slate-900 p-2.5 rounded-lg border border-slate-800">
              {selectedMetric.formula}
            </code>
          </div>

          <div className="space-y-2 text-xs">
            <span className="text-slate-400 font-bold block">Input Evidence Citation IDs:</span>
            <div className="flex flex-wrap gap-2 font-mono">
              {selectedMetric.input_evidence_ids.map(eid => (
                <span key={eid} className="px-3 py-1 bg-indigo-950 text-indigo-300 border border-indigo-800 rounded-lg">
                  [Evidence: {eid.slice(0, 8)}]
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
