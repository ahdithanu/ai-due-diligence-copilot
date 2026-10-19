import React, { useState, useEffect } from 'react';
import { ValuationCompsResponse } from '../types';

interface ValuationCompsViewProps {
  investmentId: string;
  companyName?: string;
  arr?: number;
  valuation?: number;
}

export const ValuationCompsView: React.FC<ValuationCompsViewProps> = ({
  investmentId,
  companyName = 'Acme SaaS AI',
  arr = 10000000,
  valuation = 50000000,
}) => {
  const [data, setData] = useState<ValuationCompsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [exportingExcel, setExportingExcel] = useState(false);

  const fetchComps = async () => {
    setLoading(true);
    try {
      const url = `/api/v1/investments/${investmentId}/valuation-comps?company_name=${encodeURIComponent(
        companyName
      )}&arr=${arr}&valuation=${valuation}`;
      const res = await fetch(url);
      if (res.ok) {
        const json: ValuationCompsResponse = await res.json();
        setData(json);
      }
    } catch (err) {
      console.error('Failed to fetch valuation comps', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComps();
  }, [investmentId, companyName, arr, valuation]);

  const handleDownloadExcel = async () => {
    setExportingExcel(true);
    try {
      const url = `/api/v1/investments/${investmentId}/financial-model/download-xlsx?company_name=${encodeURIComponent(
        companyName
      )}&arr=${arr}&valuation=${valuation}`;
      const res = await fetch(url);
      if (res.ok) {
        const blob = await res.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `${companyName.toLowerCase().replace(/[^a-z0-9]/g, '_')}_financial_model.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);
      }
    } catch (err) {
      console.error('Failed to export Excel model', err);
    } finally {
      setExportingExcel(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  const formatMillions = (num: number) => {
    return `$${(num / 1000000).toFixed(1)}M`;
  };

  const discountToMedian = data
    ? (((data.current_valuation_usd - data.implied_median_valuation_usd) /
        data.implied_median_valuation_usd) *
        100).toFixed(1)
    : '0';

  // Scale for football field horizontal bar (min 0 to max 200M)
  const maxScale = 200000000;

  return (
    <div className="space-y-6">
      {/* Top Banner & Excel Export */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl">🏟️</span>
              <h2 className="text-xl font-bold text-slate-100">
                Valuation Multiples &amp; Football Field Analysis
              </h2>
              <span className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs px-2.5 py-1 rounded-full font-semibold">
                Investment Banking Grade
              </span>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Cross-benchmarks target company entry valuation against Public SaaS trading comps, precedent M&amp;A transactions, DCF, and LBO floor.
            </p>
          </div>

          <button
            onClick={handleDownloadExcel}
            disabled={exportingExcel}
            className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold text-sm transition-all shadow-lg shadow-emerald-600/20"
          >
            <span>📊</span>
            {exportingExcel ? 'Generating Workbook...' : 'Export Excel Financial Model (.xlsx)'}
          </button>
        </div>

        {/* Valuation Summary Card */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6 pt-5 border-t border-slate-800">
          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Proposed Entry Valuation</div>
            <div className="text-3xl font-black text-indigo-400 mt-1">
              {formatMillions(data?.current_valuation_usd || 0)}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {((data?.current_valuation_usd || 0) / (data?.current_arr_usd || 1)).toFixed(1)}x Current ARR
            </div>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Implied Comps Median</div>
            <div className="text-3xl font-black text-emerald-400 mt-1">
              {formatMillions(data?.implied_median_valuation_usd || 0)}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {((data?.implied_median_valuation_usd || 0) / (data?.current_arr_usd || 1)).toFixed(1)}x Blended ARR
            </div>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Entry Discount / Margin</div>
            <div className="text-3xl font-black text-emerald-400 mt-1">
              {Math.abs(Number(discountToMedian))}%
            </div>
            <div className="text-xs text-emerald-500/90 font-medium mt-1">
              ✓ Attractive Entry Valuation
            </div>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Rule of 40 Scorecard</div>
            <div className="text-3xl font-black text-purple-400 mt-1">
              {data?.target_rule_of_40_pct}%
            </div>
            <div className="text-xs text-slate-400 mt-1">
              Peer Median: {data?.peer_median_rule_of_40_pct}%
            </div>
          </div>
        </div>
      </div>

      {/* Football Field Visualizer */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <span>📈</span> Valuation Football Field ($M)
          </h3>
          <span className="text-xs text-slate-400">Horizontal spans represent 25th - 75th percentile ranges</span>
        </div>

        <div className="space-y-5 pt-2">
          {data?.methodology_ranges.map((m) => {
            const leftPct = (m.low_valuation_usd / maxScale) * 100;
            const widthPct = ((m.high_valuation_usd - m.low_valuation_usd) / maxScale) * 100;
            const medianPct = (m.median_valuation_usd / maxScale) * 100;

            return (
              <div key={m.methodology_name} className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-200">{m.methodology_name}</span>
                  <span className="text-slate-400 font-mono">
                    {formatMillions(m.low_valuation_usd)} — {formatMillions(m.high_valuation_usd)} ({m.multiple_metric})
                  </span>
                </div>

                <div className="relative h-8 bg-slate-950 rounded-lg overflow-hidden border border-slate-800">
                  {/* Target Deal Reference Line */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-indigo-500 z-20 shadow-md shadow-indigo-500"
                    style={{ left: `${((data.current_valuation_usd) / maxScale) * 100}%` }}
                    title={`Proposed Deal: ${formatMillions(data.current_valuation_usd)}`}
                  ></div>

                  {/* Range Span Bar */}
                  <div
                    className="absolute top-1.5 bottom-1.5 rounded-md bg-gradient-to-r from-emerald-600/60 via-emerald-500/80 to-emerald-600/60 border border-emerald-400/50 flex items-center justify-center text-[10px] font-bold text-white shadow-sm"
                    style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                  >
                    <span className="truncate px-1">Median: {formatMillions(m.median_valuation_usd)}</span>
                  </div>

                  {/* Median Notch */}
                  <div
                    className="absolute top-0 bottom-0 w-1 bg-white z-10"
                    style={{ left: `${medianPct}%` }}
                  ></div>
                </div>
              </div>
            );
          })}

          {/* Scale Axis */}
          <div className="pt-2 flex justify-between text-[11px] font-mono text-slate-500 border-t border-slate-800">
            <span>$0M</span>
            <span>$50M (Deal Price)</span>
            <span>$100M</span>
            <span>$150M</span>
            <span>$200M</span>
          </div>
        </div>
      </div>

      {/* Public Peers Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 bg-slate-900/50">
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>🏢</span> Public SaaS Comparable Multiples (Live Peer Universe)
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950 text-xs uppercase text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Ticker</th>
                <th className="p-3">Company Name</th>
                <th className="p-3 text-right">EV / ARR Multiple</th>
                <th className="p-3 text-right">EV / EBITDA</th>
                <th className="p-3 text-right">YoY Growth %</th>
                <th className="p-3 text-right">Gross Margin %</th>
                <th className="p-3 text-right">Rule of 40</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70 font-mono">
              {data?.public_peers.map((peer) => (
                <tr key={peer.ticker} className="hover:bg-slate-850 transition-colors">
                  <td className="p-3 font-bold text-indigo-400">{peer.ticker}</td>
                  <td className="p-3 font-sans text-slate-200">{peer.name}</td>
                  <td className="p-3 text-right font-bold text-emerald-400">{peer.ev_revenue_multiple.toFixed(1)}x</td>
                  <td className="p-3 text-right text-slate-400">{peer.ev_ebitda_multiple ? `${peer.ev_ebitda_multiple.toFixed(1)}x` : '-'}</td>
                  <td className="p-3 text-right text-slate-300">{peer.growth_rate_pct.toFixed(1)}%</td>
                  <td className="p-3 text-right text-slate-300">{peer.gross_margin_pct.toFixed(1)}%</td>
                  <td className="p-3 text-right font-bold text-purple-400">{peer.rule_of_40_pct.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Precedent M&A Deals Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 bg-slate-900/50">
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>🤝</span> Precedent M&amp;A &amp; Private Equity Buyout Multiples
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950 text-xs uppercase text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Target Company</th>
                <th className="p-3">Acquiring Sponsor / Strategic</th>
                <th className="p-3">Year</th>
                <th className="p-3 text-right">EV / ARR Multiple</th>
                <th className="p-3 text-right">Total Deal Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70 font-mono">
              {data?.precedent_deals.map((deal) => (
                <tr key={deal.target} className="hover:bg-slate-850 transition-colors">
                  <td className="p-3 font-bold text-slate-200 font-sans">{deal.target}</td>
                  <td className="p-3 text-slate-300 font-sans">{deal.acquirer}</td>
                  <td className="p-3 text-slate-400">{deal.year}</td>
                  <td className="p-3 text-right font-bold text-emerald-400">{deal.ev_arr_multiple.toFixed(1)}x</td>
                  <td className="p-3 text-right text-slate-300">{formatMillions(deal.deal_size_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
