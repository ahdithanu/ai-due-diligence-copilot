import React, { useState } from 'react';
import { DiligenceState, SpecialistAnalysis } from '../types';

interface ICDebateViewProps {
  state: DiligenceState;
}

export const ICDebateView: React.FC<ICDebateViewProps> = ({ state }) => {
  const [activeTab, setActiveTab] = useState<'debate' | 'specialists' | 'contradictions'>('debate');

  const getRecommendationBadge = (rec?: string) => {
    switch (rec) {
      case 'INVEST':
        return <span className="badge-status badge-invest text-sm px-4 py-1.5">🚀 RECOMMENDATION: INVEST</span>;
      case 'PASS':
        return <span className="badge-status badge-pass text-sm px-4 py-1.5">🛑 RECOMMENDATION: PASS</span>;
      default:
        return <span className="badge-status badge-conditional text-sm px-4 py-1.5">⚠️ RECOMMENDATION: CONDITIONAL PASS</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* IC Recommendation Header */}
      <div className="glass-panel p-6 rounded-2xl border border-indigo-500/20 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
              <span>🏛️ Investment Committee Synthesis & Debate</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Adversarial synthesis of Bull, Bear, and Skeptic positions with evidence-weighted scoring.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {getRecommendationBadge(state.recommendation)}
            {state.confidence_score !== undefined && (
              <div className="bg-slate-900/90 px-4 py-2 rounded-xl border border-indigo-500/30 text-center">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Confidence</span>
                <span className="text-lg font-extrabold text-indigo-300 font-mono">
                  {(state.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Investment Thesis Summary */}
        {state.investment_thesis && (
          <div className="bg-slate-950/70 p-4.5 rounded-xl border border-slate-800 space-y-1">
            <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Executive Thesis:</span>
            <p className="text-sm text-slate-200 leading-relaxed font-sans">{state.investment_thesis}</p>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 gap-4">
        <button
          onClick={() => setActiveTab('debate')}
          className={`pb-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'debate' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Bull vs. Bear vs. Skeptic Debate
        </button>
        <button
          onClick={() => setActiveTab('specialists')}
          className={`pb-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'specialists' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Specialist Domain Analyses ({Object.keys(state.specialist_analyses).length})
        </button>
        <button
          onClick={() => setActiveTab('contradictions')}
          className={`pb-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'contradictions' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Contradictions & Open Questions ({state.contradictions.length + state.open_questions.length})
        </button>
      </div>

      {/* Debate View Grid */}
      {activeTab === 'debate' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Bull Case */}
          <div className="glass-panel p-6 rounded-2xl border border-emerald-500/30 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-emerald-900/50">
              <h3 className="text-base font-bold text-emerald-400 flex items-center gap-2">
                <span>📈 Bull Case (Upside)</span>
              </h3>
              <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                Bull Node
              </span>
            </div>
            <div className="text-xs text-slate-200 space-y-3 font-sans whitespace-pre-wrap leading-relaxed">
              {state.bull_case || 'Bull case analysis pending graph execution.'}
            </div>
          </div>

          {/* Bear Case */}
          <div className="glass-panel p-6 rounded-2xl border border-rose-500/30 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-rose-900/50">
              <h3 className="text-base font-bold text-rose-400 flex items-center gap-2">
                <span>📉 Bear Case (Downside)</span>
              </h3>
              <span className="text-xs px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">
                Bear Node
              </span>
            </div>
            <div className="text-xs text-slate-200 space-y-3 font-sans whitespace-pre-wrap leading-relaxed">
              {state.bear_case || 'Bear case analysis pending graph execution.'}
            </div>
          </div>

          {/* Skeptic Critique */}
          <div className="glass-panel p-6 rounded-2xl border border-amber-500/30 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-amber-900/50">
              <h3 className="text-base font-bold text-amber-400 flex items-center gap-2">
                <span>🧐 Skeptic Critique</span>
              </h3>
              <span className="text-xs px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                Skeptic Node
              </span>
            </div>
            <div className="text-xs text-slate-200 space-y-3 font-sans whitespace-pre-wrap leading-relaxed">
              {state.skeptic_critique || 'Skeptic critique pending graph execution.'}
            </div>
          </div>
        </div>
      )}

      {/* Specialist Analyses Grid */}
      {activeTab === 'specialists' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {Object.keys(state.specialist_analyses).length === 0 ? (
            <div className="glass-panel p-8 text-center text-slate-400 rounded-2xl col-span-2">
              No specialist analyses generated yet.
            </div>
          ) : (
            Object.entries(state.specialist_analyses).map(([domain, sa]: [string, SpecialistAnalysis]) => (
              <div key={domain} className="glass-card p-6 rounded-2xl border border-slate-800 space-y-3">
                <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                  <h4 className="font-bold text-sm text-white flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span>
                    {domain} Specialist
                  </h4>
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                    sa.passed_evaluation ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-amber-950 text-amber-300 border-amber-800'
                  }`}>
                    {sa.passed_evaluation ? 'Evaluated ✓' : 'Revision Required'}
                  </span>
                </div>

                <p className="text-xs text-slate-300 font-sans leading-relaxed">{sa.summary}</p>

                {sa.strengths && sa.strengths.length > 0 && (
                  <div className="space-y-1">
                    <span className="text-[11px] font-bold text-emerald-400 uppercase">Strengths:</span>
                    <ul className="list-disc list-inside text-xs text-slate-300 space-y-0.5">
                      {sa.strengths.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                  </div>
                )}

                {sa.concerns && sa.concerns.length > 0 && (
                  <div className="space-y-1">
                    <span className="text-[11px] font-bold text-rose-400 uppercase">Concerns:</span>
                    <ul className="list-disc list-inside text-xs text-slate-300 space-y-0.5">
                      {sa.concerns.map((c, i) => <li key={i}>{c}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Contradictions & Open Questions */}
      {activeTab === 'contradictions' && (
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Evidence Contradiction Register</h3>
          {state.contradictions.length === 0 ? (
            <div className="glass-panel p-6 text-center text-slate-400 rounded-xl">No material evidence contradictions flagged.</div>
          ) : (
            <div className="space-y-3">
              {state.contradictions.map(c => (
                <div key={c.id} className="glass-card p-4 rounded-xl border border-rose-500/30 flex items-start justify-between gap-4">
                  <div>
                    <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">
                      {c.materiality} MATERIALITY
                    </span>
                    <p className="text-xs text-slate-200 mt-2 font-medium">{c.description}</p>
                    <span className="text-[11px] text-slate-400 font-mono mt-1 block">
                      Claim A: {c.claim_a_id.slice(0, 8)} | Claim B: {c.claim_b_id.slice(0, 8)}
                    </span>
                  </div>
                  <span className="text-xs font-bold text-rose-400 uppercase font-mono">{c.status}</span>
                </div>
              ))}
            </div>
          )}

          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider pt-4">Prioritized Diligence Questions</h3>
          {state.open_questions.length === 0 ? (
            <div className="glass-panel p-6 text-center text-slate-400 rounded-xl">No open diligence questions logged.</div>
          ) : (
            <div className="space-y-3">
              {state.open_questions.map(q => (
                <div key={q.id} className="glass-card p-4 rounded-xl border border-slate-800 space-y-1.5">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                      PRIORITY #{q.priority} - {q.materiality}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono uppercase">{q.status}</span>
                  </div>
                  <p className="text-xs font-bold text-white">{q.question}</p>
                  <p className="text-xs text-slate-400">Why it matters: {q.reason_it_matters}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
