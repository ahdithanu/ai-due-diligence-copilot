import React, { useState } from 'react';

export const LPTeaserView: React.FC = () => {
  const [copiedLink, setCopiedLink] = useState<boolean>(false);

  const handleDownloadPDF = () => {
    window.print();
  };

  const handleCopyShareLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2500);
  };

  return (
    <div className="space-y-6">
      {/* Action Toolbar */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">📄</span>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Executive LP Investment Teaser (1-Pager)
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Institutional Ready
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Exportable 1-page executive summary formatted for Limited Partners (LPs), Investment Committee memo briefs, and syndicate co-investors.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleCopyShareLink}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all flex items-center gap-1.5"
          >
            <span>🔗</span>
            <span>{copiedLink ? 'Link Copied!' : 'Copy Share Link'}</span>
          </button>

          <button
            onClick={handleDownloadPDF}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md transition-all border border-indigo-500 flex items-center gap-1.5"
          >
            <span>📄</span>
            <span>Download PDF Teaser</span>
          </button>
        </div>
      </div>

      {/* Print-Ready 1-Page Document Container */}
      <div className="glass-panel p-8 sm:p-10 rounded-2xl border border-slate-800 bg-slate-950 text-slate-100 space-y-8 shadow-2xl print:bg-white print:text-black print:p-0 print:shadow-none">
        {/* Document Header */}
        <div className="border-b border-slate-800 pb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-indigo-600 text-white flex items-center justify-center font-black text-2xl shadow-lg border border-indigo-400">
              N
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-extrabold text-white tracking-tight">
                  Nexus AI Systems Inc.
                </h1>
                <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  RECOMMENDATION: INVEST
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Autonomous AI Investment Due Diligence &amp; Financial Operations Platform
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-right sm:text-left text-xs font-mono bg-slate-900/80 p-3.5 rounded-xl border border-slate-800">
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Target Round</span>
              <span className="font-bold text-white">Series B</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Check Size</span>
              <span className="font-bold text-indigo-400">$15.0M</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Post Valuation</span>
              <span className="font-bold text-emerald-400">$50.0M Cap</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block uppercase">Lead Status</span>
              <span className="font-bold text-cyan-400">Sole Lead</span>
            </div>
          </div>
        </div>

        {/* 4 Core Highlight Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase font-mono tracking-wider block">
              Current ARR
            </span>
            <div className="text-2xl font-extrabold text-white font-mono">$8.40M</div>
            <span className="text-[10px] font-bold text-emerald-400">+140% YoY Growth</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase font-mono tracking-wider block">
              Net Retention (NRR)
            </span>
            <div className="text-2xl font-extrabold text-white font-mono">118.4%</div>
            <span className="text-[10px] font-bold text-teal-400">Enterprise Cohorts</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase font-mono tracking-wider block">
              Gross Margin
            </span>
            <div className="text-2xl font-extrabold text-white font-mono">82.5%</div>
            <span className="text-[10px] font-bold text-indigo-400">SaaS Model Profile</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase font-mono tracking-wider block">
              CAC Payback
            </span>
            <div className="text-2xl font-extrabold text-white font-mono">11 Mos</div>
            <span className="text-[10px] font-bold text-cyan-400">High Capital Efficiency</span>
          </div>
        </div>

        {/* Investment Thesis & Highlights */}
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider text-indigo-400 flex items-center gap-2">
            <span>💡</span> Key Investment Thesis Highlights
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <h3 className="font-bold text-white flex items-center gap-1.5">
                <span>🚀</span> Category Creation in Autonomous AI Diligence
              </h3>
              <p className="text-slate-300 leading-relaxed">
                Nexus AI automates 80% of institutional due diligence workflows across private equity and venture capital funds, reducing deal turnaround time from 4 weeks to 48 hours.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <h3 className="font-bold text-white flex items-center gap-1.5">
                <span>🛡️</span> Proprietary Graph Verification Moat
              </h3>
              <p className="text-slate-300 leading-relaxed">
                Deterministic calculation engine prevents LLM hallucination in financial auditing with 99.4% precision across term sheets, cap tables, and revenue ledgers.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <h3 className="font-bold text-white flex items-center gap-1.5">
                <span>📈</span> Rapid Revenue Scale &amp; High Expansion
              </h3>
              <p className="text-slate-300 leading-relaxed">
                ARR grew from $3.5M to $8.4M in 12 months with net dollar expansion driven by fund managers adding associate seats and portfolio company monitoring modules.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <h3 className="font-bold text-white flex items-center gap-1.5">
                <span>🏆</span> Seasoned Founder &amp; Technical Team
              </h3>
              <p className="text-slate-300 leading-relaxed">
                Led by ex-Goldman Sachs technology partners and Stanford AI lab researchers with prior exit experience in enterprise fintech infrastructure.
              </p>
            </div>
          </div>
        </div>

        {/* Risk Register & Structure Mitigants */}
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider text-rose-400 flex items-center gap-2">
            <span>🚨</span> Core Risks &amp; Deal Structure Mitigants
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase">
                  <th className="py-2.5 px-3">Identified Risk Factor</th>
                  <th className="py-2.5 px-3">Severity</th>
                  <th className="py-2.5 px-3">Institutional Mitigant &amp; Structure</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                <tr>
                  <td className="py-3 px-3 font-semibold text-white">
                    Customer Alpha Corp Concentration (18.2% ARR)
                  </td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                      HIGH
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-300">
                    Tranche investment check ($10M upfront, $5M on Alpha Corp contract renewal execution).
                  </td>
                </tr>

                <tr>
                  <td className="py-3 px-3 font-semibold text-white">
                    Lack of SOC2 Type II Certification
                  </td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                      MEDIUM
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-300">
                    $500k dedicated security budget allocated in Series B proceeds for SOC2 Type II completion by Q4.
                  </td>
                </tr>

                <tr>
                  <td className="py-3 px-3 font-semibold text-white">
                    Valuation Compression in Downside Market
                  </td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      LOW
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-300">
                    Negotiated $50M post-money valuation cap (down from $60M founder ask) providing 1.0x liquidation pref.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Expected LP Return Profile */}
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider text-emerald-400 flex items-center gap-2">
            <span>🎯</span> LP Return Profile &amp; Exit Scenarios ($15M Check at $50M Post)
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">
                $100M M&amp;A Exit
              </span>
              <div className="text-xl font-extrabold text-amber-400 font-mono">2.00x MOIC</div>
              <span className="text-[10px] text-slate-400 block">$30.0M Return</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">
                $250M Base Exit
              </span>
              <div className="text-xl font-extrabold text-emerald-400 font-mono">5.00x MOIC</div>
              <span className="text-[10px] text-slate-400 block">$75.0M Return</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">
                $500M Growth Exit
              </span>
              <div className="text-xl font-extrabold text-cyan-400 font-mono">10.00x MOIC</div>
              <span className="text-[10px] text-slate-400 block">$150.0M Return</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">
                $1.0B IPO Exit
              </span>
              <div className="text-xl font-extrabold text-indigo-400 font-mono">20.00x MOIC</div>
              <span className="text-[10px] text-slate-400 block">$300.0M Return</span>
            </div>
          </div>
        </div>

        {/* Footer Audit Stamp */}
        <div className="pt-6 border-t border-slate-800 flex justify-between items-center text-[10px] text-slate-500 font-mono">
          <span>CONFIDENTIAL - Prepared for Investment Committee &amp; Limited Partners</span>
          <span>Generated by Institutional Diligence Copilot • Aug 2026</span>
        </div>
      </div>
    </div>
  );
};
