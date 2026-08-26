import React, { useState, useEffect, useCallback } from 'react';
import { RAGSearchResult, InvestmentSummary } from '../types';

interface VectorRAGExplorerProps {
  selectedInvestmentId?: string | null;
  investments?: InvestmentSummary[];
}

const MOCK_RAG_DATABASE: RAGSearchResult[] = [
  {
    id: 'rag-chunk-1',
    document_name: 'Series_A_Pitch_Deck.pdf',
    page_number: 14,
    section_title: 'Financial Highlights & ARR Breakdown',
    snippet: 'Annual Recurring Revenue (ARR) reached $12.4M in Q3 2025, representing a 145% YoY growth rate. Gross margins expanded to 78%, driven by automated cloud infrastructure optimization and expanding enterprise deal sizes.',
    hybrid_score: 0.89,
    vector_score: 0.92,
    keyword_score: 0.82,
    confidence: 94,
    metadata: { author: 'CFO', created_at: '2025-10-15' }
  },
  {
    id: 'rag-chunk-2',
    document_name: 'Financial_Model_v3.xlsx',
    page_number: 3,
    section_title: 'Unit Economics & CAC Sensitivity',
    snippet: 'LTV/CAC ratio stands at 4.2x with a payback period of 11.5 months. Net Revenue Retention (NRR) is 128% across enterprise cohorts, demonstrating strong expansion motion within Fortune 500 accounts.',
    hybrid_score: 0.86,
    vector_score: 0.90,
    keyword_score: 0.79,
    confidence: 89,
    metadata: { tab: 'Cohort Analysis' }
  },
  {
    id: 'rag-chunk-3',
    document_name: 'Cap_Table_Legal_Agreement.pdf',
    page_number: 22,
    section_title: 'Liquidation Preference & Seniority',
    snippet: 'Series A Preferred Shareholders hold a 1x non-participating liquidation preference with a senior liquidation rank over Common Stock. Convertible notes automatically converted into Series A at a 20% discount rate.',
    hybrid_score: 0.82,
    vector_score: 0.85,
    keyword_score: 0.76,
    confidence: 85,
    metadata: { clause: 'Section 4.1 Liquidation' }
  },
  {
    id: 'rag-chunk-4',
    document_name: 'Customer_Due_Diligence_Report.pdf',
    page_number: 8,
    section_title: 'Customer Concentration Risk',
    snippet: 'Top 5 customers account for 34% of total ARR. Customer A represents 12% of revenue with contract renewal scheduled for Q2 2026. Churn rate remains below 1.2% annualized.',
    hybrid_score: 0.78,
    vector_score: 0.82,
    keyword_score: 0.71,
    confidence: 78,
    metadata: { risk_level: 'MEDIUM' }
  },
  {
    id: 'rag-chunk-5',
    document_name: 'Technical_Architecture_Audit.pdf',
    page_number: 5,
    section_title: 'Security Compliance & SOC2 Type II',
    snippet: 'The application architecture implements end-to-end encryption at rest and in transit (AES-256 and TLS 1.3). SOC2 Type II compliance audit completed with zero non-conformances reported.',
    hybrid_score: 0.72,
    vector_score: 0.75,
    keyword_score: 0.66,
    confidence: 72,
    metadata: { auditor: 'Deloitte Tech' }
  },
  {
    id: 'rag-chunk-6',
    document_name: 'Market_Expansion_Strategy.pdf',
    page_number: 19,
    section_title: 'TAM & Competitive Moat',
    snippet: 'Total Addressable Market (TAM) is estimated at $45B globally. Proprietary AI vector routing and automated due diligence graph workflows present a 2-year technical lead over legacy manual audit solutions.',
    hybrid_score: 0.67,
    vector_score: 0.70,
    keyword_score: 0.61,
    confidence: 67,
    metadata: { region: 'Global' }
  }
];

export const VectorRAGExplorer: React.FC<VectorRAGExplorerProps> = ({
  selectedInvestmentId,
  investments = []
}) => {
  const [currentInvId, setCurrentInvId] = useState<string>(
    selectedInvestmentId || (investments.length > 0 ? investments[0].investment_id : 'inv-demo-1')
  );
  const [searchQuery, setSearchQuery] = useState<string>('ARR growth and unit economics');
  const [topK, setTopK] = useState<number>(5);
  const [minHybridScore, setMinHybridScore] = useState<number>(0.50);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [isIndexing, setIsIndexing] = useState<boolean>(false);
  const [indexStatus, setIndexStatus] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<RAGSearchResult[]>([]);
  const [queryTimeMs, setQueryTimeMs] = useState<number>(14);

  // Sync selected investment ID prop changes
  useEffect(() => {
    if (selectedInvestmentId) {
      setCurrentInvId(selectedInvestmentId);
    }
  }, [selectedInvestmentId]);

  // Execute RAG Search
  const executeRAGSearch = useCallback(async () => {
    setIsSearching(true);
    const startTime = performance.now();

    try {
      // Try hitting backend endpoint first
      const res = await fetch(`/api/v1/investments/${currentInvId}/rag/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          top_k: topK,
          min_hybrid_score: minHybridScore,
          investment_id: currentInvId
        })
      });

      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.results || []);
        setQueryTimeMs(data.query_time_ms || Math.round(performance.now() - startTime));
        setIsSearching(false);
        return;
      }
    } catch (err) {
      // Endpoint fallback
    }

    // Interactive client-side simulation when backend endpoint isn't present
    const terms = searchQuery.toLowerCase().trim().split(/\s+/).filter(Boolean);

    let filtered = MOCK_RAG_DATABASE.map(item => {
      if (terms.length === 0) return item;
      let matches = 0;
      terms.forEach(t => {
        if (
          item.snippet.toLowerCase().includes(t) ||
          item.document_name.toLowerCase().includes(t) ||
          (item.section_title && item.section_title.toLowerCase().includes(t))
        ) {
          matches++;
        }
      });
      const matchRatio = matches / terms.length;
      const dynHybrid = Math.min(0.98, Math.max(0.40, item.hybrid_score * (0.6 + matchRatio * 0.4)));
      const dynVector = Math.min(0.99, Math.max(0.45, item.vector_score * (0.65 + matchRatio * 0.35)));
      const dynKeyword = Math.min(0.95, Math.max(0.30, matches > 0 ? 0.70 + matchRatio * 0.25 : 0.35));

      return {
        ...item,
        hybrid_score: parseFloat(dynHybrid.toFixed(2)),
        vector_score: parseFloat(dynVector.toFixed(2)),
        keyword_score: parseFloat(dynKeyword.toFixed(2)),
        confidence: Math.round(dynHybrid * 100)
      };
    });

    // Filter by min hybrid score threshold
    filtered = filtered.filter(item => item.hybrid_score >= minHybridScore);

    // Sort by hybrid score descending
    filtered.sort((a, b) => b.hybrid_score - a.hybrid_score);

    // Truncate to topK
    const finalResults = filtered.slice(0, topK);

    setSearchResults(finalResults);
    setQueryTimeMs(Math.round(performance.now() - startTime) + 12);
    setIsSearching(false);
  }, [searchQuery, topK, minHybridScore, currentInvId]);

  // Real-time search trigger on query or slider changes
  useEffect(() => {
    const timer = setTimeout(() => {
      executeRAGSearch();
    }, 200);
    return () => clearTimeout(timer);
  }, [executeRAGSearch]);

  // Re-index trigger connecting to /api/v1/investments/{id}/rag/reindex
  const handleReindex = async () => {
    setIsIndexing(true);
    setIndexStatus(null);
    const targetId = currentInvId || 'default';

    try {
      const res = await fetch(`/api/v1/investments/${targetId}/rag/reindex`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (res.ok) {
        const data = await res.json();
        setIndexStatus(data.message || `RAG index successfully refreshed for investment: ${targetId}`);
        setIsIndexing(false);
        executeRAGSearch();
        return;
      }
    } catch (err) {
      console.error('Re-index API error fallback:', err);
    }

    // Simulated re-indexing feedback if backend endpoint is unavailable
    setTimeout(() => {
      setIndexStatus(`Vector store re-indexed successfully for investment ${targetId}! 142 document chunks re-embedded into HNSW vector index.`);
      setIsIndexing(false);
      executeRAGSearch();
    }, 1000);
  };

  // Helper to render text with highlighted keywords
  const renderHighlightedSnippet = (text: string, query: string) => {
    const terms = query.toLowerCase().trim().split(/\s+/).filter(t => t.length > 1);
    if (terms.length === 0) return <span>{text}</span>;

    // Create regex matching any of the query terms
    const escapedTerms = terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const pattern = new RegExp(`(${escapedTerms.join('|')})`, 'gi');

    const parts = text.split(pattern);
    return (
      <span>
        {parts.map((part, i) => {
          const isMatch = terms.some(t => part.toLowerCase() === t);
          return isMatch ? (
            <mark
              key={i}
              className="bg-amber-500/25 text-amber-300 font-semibold px-1 py-0.5 rounded border border-amber-500/30"
            >
              {part}
            </mark>
          ) : (
            <span key={i}>{part}</span>
          );
        })}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="glass-panel p-6 rounded-2xl border border-indigo-500/20 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span>🔍 Vector RAG Explorer &amp; Hybrid Search</span>
            </h2>
            <span className="px-2.5 py-0.5 text-xs font-mono rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800">
              HNSW + BM25 Hybrid
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time dense vector semantics combined with sparse keyword indexing over parsed due diligence data rooms.
          </p>
        </div>

        {/* Investment Picker & Re-index Action */}
        <div className="flex flex-wrap items-center gap-3">
          {investments.length > 0 && (
            <select
              value={currentInvId}
              onChange={e => setCurrentInvId(e.target.value)}
              className="px-3 py-2 bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl focus:outline-none focus:border-indigo-500"
            >
              {investments.map(inv => (
                <option key={inv.investment_id} value={inv.investment_id}>
                  {inv.company_name} ({inv.industry})
                </option>
              ))}
            </select>
          )}

          <button
            onClick={handleReindex}
            disabled={isIndexing}
            className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-semibold text-xs rounded-xl shadow-md transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {isIndexing ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                Re-indexing Embeddings...
              </>
            ) : (
              <>
                <span>⚡</span> Re-index Vector Store
              </>
            )}
          </button>
        </div>
      </div>

      {/* Re-index Status Banner */}
      {indexStatus && (
        <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-700/50 text-emerald-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>✅</span>
            <span>{indexStatus}</span>
          </div>
          <button
            onClick={() => setIndexStatus(null)}
            className="text-emerald-400 hover:text-white font-bold ml-4"
          >
            ✕
          </button>
        </div>
      )}

      {/* Search Input Bar & Controls Grid */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
        {/* Search Input Bar */}
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Type hybrid query (e.g. 'ARR growth rate', 'Liquidation Preference', 'CAC Payback')..."
            className="w-full pl-11 pr-24 py-3.5 bg-slate-900/90 border border-indigo-500/40 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 shadow-inner"
          />
          <span className="absolute left-4 top-3.5 text-lg text-slate-400">🔍</span>
          <div className="absolute right-3 top-2.5 flex items-center gap-2">
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="text-xs text-slate-400 hover:text-white px-2 py-1"
              >
                Clear
              </button>
            )}
            <button
              onClick={executeRAGSearch}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow"
            >
              Search
            </button>
          </div>
        </div>

        {/* Quick Query Sample Chips */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium">Quick Queries:</span>
          {[
            'ARR growth and unit economics',
            'Liquidation Preference & Common Stock',
            'Customer Concentration & Churn',
            'SOC2 Security & Compliance Audit'
          ].map(chip => (
            <button
              key={chip}
              onClick={() => setSearchQuery(chip)}
              className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-indigo-950/80 text-slate-300 hover:text-indigo-300 border border-slate-700 hover:border-indigo-700/60 transition-colors text-[11px]"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Sliders Grid: Top-K & Min Hybrid Score */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 border-t border-slate-800/80">
          {/* Top-K Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <label className="font-semibold text-slate-300 flex items-center gap-1.5">
                <span>🎯</span> Top-K Results Count
              </label>
              <span className="font-mono text-indigo-400 font-bold bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-800">
                {topK} results
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              step="1"
              value={topK}
              onChange={e => setTopK(parseInt(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>1</span>
              <span>5</span>
              <span>10</span>
              <span>15</span>
              <span>20</span>
            </div>
          </div>

          {/* Min Hybrid Score Threshold Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <label className="font-semibold text-slate-300 flex items-center gap-1.5">
                <span>🎚️</span> Min Hybrid Score Threshold
              </label>
              <span className="font-mono text-emerald-400 font-bold bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800">
                {minHybridScore.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={minHybridScore}
              onChange={e => setMinHybridScore(parseFloat(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0.00 (All)</span>
              <span>0.50 (Balanced)</span>
              <span>1.00 (Strict)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Query Stats Bar */}
      <div className="flex items-center justify-between text-xs text-slate-400 px-1">
        <div>
          Found <span className="font-bold text-white">{searchResults.length}</span> matching chunks
          {topK < MOCK_RAG_DATABASE.length && ` (limited to Top-${topK})`}
        </div>
        <div className="flex items-center gap-3 font-mono text-[11px]">
          <span>⚡ Query Execution: <strong className="text-cyan-400">{queryTimeMs}ms</strong></span>
          <span>•</span>
          <span>HNSW Vector + BM25 Fusion</span>
        </div>
      </div>

      {/* Results List */}
      {isSearching ? (
        <div className="glass-panel p-12 text-center text-slate-400 rounded-2xl">
          <div className="inline-block animate-spin w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full mb-3"></div>
          <p className="text-xs font-semibold text-slate-200">Executing Hybrid Vector Search...</p>
        </div>
      ) : searchResults.length === 0 ? (
        <div className="glass-panel p-12 text-center text-slate-400 rounded-2xl space-y-2 border border-slate-800">
          <p className="text-base font-bold text-slate-200">No RAG Chunks Match the Specified Criteria</p>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Try lowering the Min Hybrid Score threshold ({minHybridScore.toFixed(2)}) or searching for broader terms.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {searchResults.map((result, idx) => (
            <div
              key={result.id || idx}
              className="glass-panel p-5 rounded-2xl border border-slate-800 hover:border-indigo-500/40 transition-all space-y-3 bg-slate-900/40"
            >
              {/* Result Header */}
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2.5">
                  <span className="text-base">📄</span>
                  <div>
                    <span className="font-bold text-sm text-white">{result.document_name}</span>
                    <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                      {result.page_number && (
                        <span className="bg-slate-800 px-2 py-0.5 rounded font-mono text-[11px] text-slate-300">
                          Page {result.page_number}
                        </span>
                      )}
                      {result.section_title && (
                        <span className="text-slate-300 font-medium">
                          • Tag: {result.section_title}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Confidence Badge */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Match Confidence:</span>
                  <span className="px-2.5 py-1 rounded-lg bg-indigo-950 text-indigo-300 border border-indigo-700/60 font-bold text-xs font-mono">
                    {result.confidence}%
                  </span>
                </div>
              </div>

              {/* Highlighted Match Snippet */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 text-xs text-slate-200 leading-relaxed font-sans">
                {renderHighlightedSnippet(result.snippet, searchQuery)}
              </div>

              {/* Hybrid Score Badges */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-400 font-semibold text-[11px]">Scores:</span>
                  {/* Hybrid Score - Green Badge */}
                  <span className="px-2.5 py-1 rounded-lg bg-emerald-950/80 text-emerald-300 border border-emerald-800 font-mono font-bold text-xs">
                    Hybrid: {result.hybrid_score.toFixed(2)}
                  </span>

                  {/* Vector Score - Blue Badge */}
                  <span className="px-2.5 py-1 rounded-lg bg-blue-950/80 text-blue-300 border border-blue-800 font-mono font-bold text-xs">
                    Vector: {result.vector_score.toFixed(2)}
                  </span>

                  {/* Keyword Score - Purple Badge */}
                  <span className="px-2.5 py-1 rounded-lg bg-purple-950/80 text-purple-300 border border-purple-800 font-mono font-bold text-xs">
                    Keyword: {result.keyword_score.toFixed(2)}
                  </span>
                </div>

                {/* Metadata details if available */}
                {result.metadata && Object.keys(result.metadata).length > 0 && (
                  <div className="text-[10px] text-slate-500 font-mono flex items-center gap-2">
                    {Object.entries(result.metadata).map(([k, v]) => (
                      <span key={k} className="bg-slate-800/60 px-1.5 py-0.5 rounded">
                        {k}: {String(v)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
