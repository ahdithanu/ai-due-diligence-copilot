import React, { useState, useEffect } from 'react';
import { ExternalIntelligenceResponse } from '../types';

interface ExternalIntelligenceViewProps {
  investmentId: string;
  companyName?: string;
}

export const ExternalIntelligenceView: React.FC<ExternalIntelligenceViewProps> = ({
  investmentId,
  companyName = 'Acme SaaS AI',
}) => {
  const [data, setData] = useState<ExternalIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchIntel = async () => {
    setLoading(true);
    try {
      const url = `/api/v1/investments/${investmentId}/external-intel?company_name=${encodeURIComponent(
        companyName
      )}`;
      const res = await fetch(url);
      if (res.ok) {
        const json: ExternalIntelligenceResponse = await res.json();
        setData(json);
      }
    } catch (err) {
      console.error('Failed to load external intelligence', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntel();
  }, [investmentId, companyName]);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  const formatMillions = (num: number) => `$${(num / 1000000).toFixed(1)}M`;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl">🌐</span>
              <h2 className="text-xl font-bold text-slate-100">
                External Market &amp; Executive Intelligence Radar
              </h2>
              <span className="bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs px-2.5 py-1 rounded-full font-semibold">
                PitchBook &amp; Crunchbase Feed
              </span>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Cross-verifies self-reported data rooms against public fundraising history, direct competitor market share, key executive flight risks, and Glassdoor organizational health signals.
            </p>
          </div>
        </div>

        {/* Organizational Health KPI Gauges */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6 pt-5 border-t border-slate-800">
          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Glassdoor Employer Score</div>
            <div className="text-3xl font-black text-emerald-400 mt-1 flex items-baseline gap-1">
              {data?.org_health.glassdoor_rating}{' '}
              <span className="text-xs font-normal text-slate-500">/ 5.0</span>
            </div>
            <div className="text-xs text-emerald-400 font-medium mt-1">
              ★ 94% CEO Approval Rating
            </div>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Total Headcount &amp; Growth</div>
            <div className="text-3xl font-black text-indigo-400 mt-1">
              {data?.org_health.headcount_total}{' '}
              <span className="text-xs font-normal text-slate-400">FTEs</span>
            </div>
            <div className="text-xs text-emerald-400 font-medium mt-1">
              +{data?.org_health.yoy_headcount_growth_pct}% YoY Expansion
            </div>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Annual Regretted Attrition</div>
            <div className="text-3xl font-black text-emerald-400 mt-1">
              {data?.org_health.annual_regretted_attrition_pct}%
            </div>
            <div className="text-xs text-slate-400 mt-1">
              vs 14.5% Tech Industry Avg
            </div>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs text-slate-400 font-semibold uppercase">Engineering Velocity Index</div>
            <div className="text-3xl font-black text-purple-400 mt-1">
              {data?.org_health.engineering_velocity_score}{' '}
              <span className="text-xs font-normal text-slate-500">/ 100</span>
            </div>
            <div className="text-xs text-slate-400 mt-1">
              Top Decile Commit Frequency
            </div>
          </div>
        </div>
      </div>

      {/* Section 1: Funding Round History Staircase */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
        <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
          <span>📈</span> Historical Capitalization &amp; Valuation Escalation
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data?.funding_history.map((round) => (
            <div
              key={round.round_name}
              className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-2 relative overflow-hidden"
            >
              <div className="flex justify-between items-start">
                <span className="text-xs font-bold text-indigo-400 font-mono">{round.date}</span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-bold">
                  {round.dilution_pct.toFixed(1)}% Dilution
                </span>
              </div>
              <h4 className="font-bold text-slate-100 text-base">{round.round_name}</h4>
              <div className="flex justify-between items-baseline pt-2 border-t border-slate-800/80">
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase font-semibold">Raised</span>
                  <span className="text-base font-bold text-emerald-400 font-mono">
                    {formatMillions(round.amount_raised_usd)}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 block uppercase font-semibold">Post-Money</span>
                  <span className="text-base font-bold text-indigo-400 font-mono">
                    {formatMillions(round.post_money_valuation_usd)}
                  </span>
                </div>
              </div>
              <div className="text-[11px] text-slate-400 pt-1">
                Leads: <span className="text-slate-300 font-medium">{round.lead_investors.join(', ')}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 2: Direct Market Competitors */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>⚔️</span> Direct Competitor Landscape (PitchBook / Crunchbase Signals)
          </h3>
          <span className="text-xs text-slate-400">Benchmarked against target ARR &amp; capital raised</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950 text-xs uppercase text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Competitor Name</th>
                <th className="p-3">Headquarters</th>
                <th className="p-3 text-right">Total Raised</th>
                <th className="p-3 text-right">Estimated ARR</th>
                <th className="p-3">Growth Momentum</th>
                <th className="p-3">Market Positioning &amp; Differentiator</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {data?.competitors.map((comp) => (
                <tr key={comp.name} className="hover:bg-slate-850 transition-colors">
                  <td className="p-3 font-semibold text-slate-100">{comp.name}</td>
                  <td className="p-3 text-xs text-slate-400">{comp.headquarters}</td>
                  <td className="p-3 text-right font-mono font-bold text-slate-200">
                    {formatMillions(comp.total_raised_usd)}
                  </td>
                  <td className="p-3 text-right font-mono font-bold text-emerald-400">
                    {formatMillions(comp.estimated_arr_usd)}
                  </td>
                  <td className="p-3">
                    <span
                      className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                        comp.growth_momentum === 'HIGH'
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                          : comp.growth_momentum === 'MODERATE'
                          ? 'bg-amber-950 text-amber-300 border border-amber-800'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {comp.growth_momentum}
                    </span>
                  </td>
                  <td className="p-3 text-xs text-slate-400 max-w-xs">{comp.key_differentiator}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 3: Executive Team & Key-Person Flight Risk Audit */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
        <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
          <span>👥</span> Executive Leadership Pedigree &amp; Flight Risk Audit
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {data?.executive_team.map((exec) => (
            <div
              key={exec.name}
              className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-2 hover:border-slate-700 transition-all"
            >
              <div className="flex justify-between items-start">
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider border ${
                    exec.flight_risk_level === 'LOW'
                      ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                      : exec.flight_risk_level === 'MEDIUM'
                      ? 'bg-amber-950 text-amber-300 border-amber-700'
                      : 'bg-rose-950 text-rose-300 border-rose-700'
                  }`}
                >
                  {exec.flight_risk_level} Flight Risk
                </span>
                <span className="font-mono text-xs font-bold text-indigo-400">
                  {exec.equity_ownership_pct}% Equity
                </span>
              </div>
              <div>
                <h4 className="font-bold text-slate-100 text-sm">{exec.name}</h4>
                <div className="text-xs text-indigo-300 font-medium">{exec.title}</div>
                <div className="text-[11px] text-slate-400">{exec.tenure_years} Years Tenure</div>
              </div>
              <div className="text-xs text-slate-300 bg-slate-900/80 p-2 rounded border border-slate-800/80">
                <span className="text-[10px] text-slate-500 block uppercase font-semibold">Pedigree</span>
                {exec.prior_pedigree}
              </div>
              <p className="text-[11px] text-slate-400 italic pt-1">{exec.status_notes}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
