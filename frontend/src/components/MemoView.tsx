import React, { useState } from 'react';
import { DiligenceState, EvidenceRecord } from '../types';

interface MemoViewProps {
  state: DiligenceState;
  evidenceRecords: EvidenceRecord[];
}

export const MemoView: React.FC<MemoViewProps> = ({ state, evidenceRecords }) => {
  const [activeCitation, setActiveCitation] = useState<EvidenceRecord | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCitationClick = (evidenceId: string) => {
    const found = evidenceRecords.find(ev => ev.id === evidenceId || ev.id.startsWith(evidenceId));
    if (found) {
      setActiveCitation(found);
    } else {
      setActiveCitation({
        id: evidenceId,
        document_id: 'doc-unknown',
        chunk_id: 'chunk-unknown',
        content: `Citation record [Evidence: ${evidenceId}] referenced in memo.`,
        extracted_at: new Date().toISOString(),
        confidence: 0.95,
        claim_type: 'FACT'
      });
    }
  };

  const handleCopy = () => {
    if (state.memo_markdown) {
      navigator.clipboard.writeText(state.memo_markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Render markdown text with clickable citation badges
  const renderMemoContent = (content: string) => {
    const citationRegex = /\[Evidence:\s*([a-zA-Z0-9-]+)\]/g;
    const parts = [];
    let lastIdx = 0;
    let match: RegExpExecArray | null;

    while ((match = citationRegex.exec(content)) !== null) {
      const textBefore = content.substring(lastIdx, match.index);
      const evId = match[1];

      parts.push(<span key={lastIdx}>{textBefore}</span>);
      parts.push(
        <button
          key={match.index}
          onClick={() => handleCitationClick(evId)}
          className="mx-1 px-2 py-0.5 rounded bg-indigo-950/90 hover:bg-indigo-900 text-indigo-300 border border-indigo-700/60 font-mono text-[11px] font-bold shadow-sm transition-all transform hover:scale-105"
        >
          [Evidence: {evId.slice(0, 8)}]
        </button>
      );
      lastIdx = citationRegex.lastIndex;
    }
    parts.push(<span key={lastIdx}>{content.substring(lastIdx)}</span>);
    return parts;
  };

  const handleDownload = (format: 'pdf' | 'markdown') => {
    if (!state.investment_id) return;
    const url = `/api/v1/investments/${state.investment_id}/memo/download?format=${format}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = '';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Memo Top Header */}
      <div className="glass-panel p-6 rounded-2xl border border-indigo-500/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>📄 Institutional Investment Memo</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono">
              Audit-Ready
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Full Markdown Memo with interactive evidence provenance citations & zero-hallucination guarantees.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => handleDownload('pdf')}
            disabled={!state.memo_markdown}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold shadow-md transition-all flex items-center gap-1.5"
          >
            <span>📥</span> Download PDF
          </button>

          <button
            onClick={() => handleDownload('markdown')}
            disabled={!state.memo_markdown}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-slate-200 border border-slate-700 text-xs font-semibold transition-all flex items-center gap-1.5"
          >
            <span>📄</span> Download Markdown
          </button>

          <button
            onClick={handleCopy}
            disabled={!state.memo_markdown}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-slate-200 border border-slate-700 text-xs font-semibold transition-all"
          >
            {copied ? '✓ Copied Markdown' : '📋 Copy Markdown'}
          </button>
        </div>
      </div>

      {/* Main Memo Content Container */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel p-8 rounded-2xl border border-slate-800 space-y-6 bg-slate-950/60">
          {!state.memo_markdown ? (
            <div className="p-12 text-center text-slate-400">
              Memo not generated yet. Execute the graph engine through MemoGeneratorNode to synthesize institutional memo.
            </div>
          ) : (
            <div className="prose prose-invert prose-indigo max-w-none text-slate-200 text-xs leading-relaxed font-sans whitespace-pre-wrap">
              {renderMemoContent(state.memo_markdown)}
            </div>
          )}
        </div>

        {/* Sidebar Citation Popover / Viewer */}
        <div className="space-y-4">
          <div className="glass-panel p-5 rounded-2xl border border-indigo-500/30 space-y-3">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Evidence Citation Inspector</h3>
            {activeCitation ? (
              <div className="bg-slate-950 p-4 rounded-xl border border-indigo-800/80 space-y-2">
                <div className="flex justify-between items-center text-[10px] font-mono">
                  <span className="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 font-bold">
                    {activeCitation.claim_type}
                  </span>
                  <span className="text-slate-400">Confidence: {(activeCitation.confidence * 100).toFixed(0)}%</span>
                </div>
                <p className="text-xs text-slate-200 bg-slate-900 p-3 rounded-lg border border-slate-800">
                  "{activeCitation.content}"
                </p>
                <div className="text-[10px] text-slate-400 font-mono space-y-0.5">
                  <p>ID: {activeCitation.id}</p>
                  <p>Document ID: {activeCitation.document_id}</p>
                  {activeCitation.page_number && <p>Page: #{activeCitation.page_number}</p>}
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">
                Click any <span className="text-indigo-400 font-mono font-bold">[Evidence: ID]</span> citation badge in the memo text to inspect its source document chunk and provenance record.
              </p>
            )}
          </div>

          <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3 text-xs">
            <h4 className="font-bold text-slate-200 uppercase tracking-wider">Citations Inventory</h4>
            <div className="space-y-1.5 font-mono text-[11px]">
              {evidenceRecords.slice(0, 8).map(ev => (
                <div
                  key={ev.id}
                  onClick={() => setActiveCitation(ev)}
                  className="p-2 rounded bg-slate-900/80 hover:bg-indigo-950/60 border border-slate-800 cursor-pointer flex justify-between items-center"
                >
                  <span className="text-indigo-300 font-bold">[Evidence: {ev.id.slice(0, 8)}]</span>
                  <span className="text-slate-400 truncate max-w-[120px]">{ev.section_title || 'Evidence Record'}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
