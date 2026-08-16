import React, { useState } from 'react';
import { EvidenceRecord, DocumentChunk, ClaimType } from '../types';

interface EvidenceExplorerProps {
  documents: Array<Record<string, any>>;
  chunks: DocumentChunk[];
  evidenceRecords: EvidenceRecord[];
  onUploadDocument: (file: File, docType: string) => Promise<void>;
}

export const EvidenceExplorer: React.FC<EvidenceExplorerProps> = ({
  documents,
  chunks,
  evidenceRecords,
  onUploadDocument
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClaimType, setSelectedClaimType] = useState<string>('ALL');
  const [selectedDocType, setSelectedDocType] = useState<string>('OTHER');
  const [uploading, setUploading] = useState(false);
  const [activeTab, setActiveTab] = useState<'evidence' | 'chunks' | 'documents'>('evidence');

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setUploading(true);
    try {
      await onUploadDocument(file, selectedDocType);
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const filteredEvidence = evidenceRecords.filter(ev => {
    const matchesSearch = ev.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (ev.section_title && ev.section_title.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = selectedClaimType === 'ALL' || ev.claim_type === selectedClaimType;
    return matchesSearch && matchesType;
  });

  const getClaimTypeColor = (type: ClaimType) => {
    switch (type) {
      case 'FACT': return 'bg-cyan-950/80 text-cyan-300 border-cyan-800';
      case 'CALCULATION': return 'bg-emerald-950/80 text-emerald-300 border-emerald-800';
      case 'INFERENCE': return 'bg-indigo-950/80 text-indigo-300 border-indigo-800';
      case 'ASSUMPTION': return 'bg-amber-950/80 text-amber-300 border-amber-800';
      case 'UNRESOLVED_QUESTION': return 'bg-rose-950/80 text-rose-300 border-rose-800';
      default: return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload & Search Controls Header */}
      <div className="glass-panel p-6 rounded-2xl border border-indigo-500/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>📁 Evidence & Provenance Explorer</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Raw document chunks, extracted claim records, and mathematical evidence links.
          </p>
        </div>

        {/* Upload Form */}
        <div className="flex items-center gap-3">
          <select
            value={selectedDocType}
            onChange={e => setSelectedDocType(e.target.value)}
            className="px-3 py-2 bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl focus:outline-none"
          >
            <option value="PITCH_DECK">Pitch Deck</option>
            <option value="FINANCIAL_STATEMENT">Financial Statement</option>
            <option value="OPERATING_METRICS">Operating Metrics</option>
            <option value="MARKET_RESEARCH">Market Research</option>
            <option value="CUSTOMER_INFO">Customer Info</option>
            <option value="OTHER">Other Material</option>
          </select>

          <label className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl cursor-pointer shadow-md transition-all inline-flex items-center gap-2">
            {uploading ? 'Uploading & Parsing...' : '+ Upload Document'}
            <input
              type="file"
              onChange={handleFileChange}
              disabled={uploading}
              className="hidden"
              accept=".pdf,.txt,.md,.json,.csv"
            />
          </label>
        </div>
      </div>

      {/* Tabs Bar */}
      <div className="flex border-b border-slate-800 gap-4">
        <button
          onClick={() => setActiveTab('evidence')}
          className={`pb-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'evidence' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Extracted Evidence ({evidenceRecords.length})
        </button>
        <button
          onClick={() => setActiveTab('chunks')}
          className={`pb-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'chunks' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Document Chunks ({chunks.length})
        </button>
        <button
          onClick={() => setActiveTab('documents')}
          className={`pb-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'documents' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Source Documents ({documents.length})
        </button>
      </div>

      {/* Search & Filters */}
      {activeTab === 'evidence' && (
        <div className="flex flex-col md:flex-row gap-3">
          <input
            type="text"
            placeholder="Search evidence claims, topics, or keywords..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="flex-1 px-4 py-2.5 bg-slate-900 border border-slate-800 text-slate-100 text-xs rounded-xl focus:outline-none focus:border-indigo-500"
          />
          <select
            value={selectedClaimType}
            onChange={e => setSelectedClaimType(e.target.value)}
            className="px-4 py-2.5 bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-xl focus:outline-none"
          >
            <option value="ALL">All Claim Types</option>
            <option value="FACT">Facts</option>
            <option value="CALCULATION">Calculations</option>
            <option value="INFERENCE">Inferences</option>
            <option value="ASSUMPTION">Assumptions</option>
            <option value="UNRESOLVED_QUESTION">Unresolved Questions</option>
          </select>
        </div>
      )}

      {/* Evidence List */}
      {activeTab === 'evidence' && (
        <div className="space-y-3">
          {filteredEvidence.length === 0 ? (
            <div className="glass-panel p-8 text-center text-slate-400 rounded-2xl">
              No evidence records match the selected filters.
            </div>
          ) : (
            filteredEvidence.map(ev => (
              <div key={ev.id} className="glass-card p-5 rounded-2xl space-y-3 border border-slate-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${getClaimTypeColor(ev.claim_type)}`}>
                      {ev.claim_type}
                    </span>
                    {ev.section_title && (
                      <span className="text-xs font-semibold text-slate-300">
                        {ev.section_title}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                    {ev.page_number && <span>Page #{ev.page_number}</span>}
                    <span>Confidence: {(ev.confidence * 100).toFixed(0)}%</span>
                    <span className="text-indigo-400 font-bold">ID: {ev.id.slice(0, 8)}</span>
                  </div>
                </div>

                <p className="text-sm text-slate-100 font-sans leading-relaxed bg-slate-950/50 p-3.5 rounded-xl border border-slate-800/80">
                  "{ev.content}"
                </p>

                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 font-mono">
                  <span>Document ID: {ev.document_id.slice(0, 8)} | Chunk ID: {ev.chunk_id.slice(0, 8)}</span>
                  <span>Extracted: {new Date(ev.extracted_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Chunks List */}
      {activeTab === 'chunks' && (
        <div className="space-y-3">
          {chunks.length === 0 ? (
            <div className="glass-panel p-8 text-center text-slate-400 rounded-2xl">No document chunks parsed yet.</div>
          ) : (
            chunks.map(chunk => (
              <div key={chunk.id} className="glass-card p-4 rounded-xl space-y-2 border border-slate-800">
                <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                  <span className="font-bold text-slate-200">Chunk #{chunk.chunk_index}</span>
                  <span>Page {chunk.page_number || 1} | {chunk.char_count} chars</span>
                </div>
                <p className="text-xs text-slate-300 font-mono bg-slate-950 p-3 rounded-lg border border-slate-800 whitespace-pre-wrap">
                  {chunk.content}
                </p>
              </div>
            ))
          )}
        </div>
      )}

      {/* Documents List */}
      {activeTab === 'documents' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {documents.length === 0 ? (
            <div className="glass-panel p-8 text-center text-slate-400 rounded-2xl col-span-2">No uploaded documents.</div>
          ) : (
            documents.map((doc, idx) => (
              <div key={idx} className="glass-card p-5 rounded-2xl space-y-2 border border-slate-800">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-white">{doc.filename}</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                    {doc.doc_type || 'OTHER'}
                  </span>
                </div>
                <div className="text-xs text-slate-400 font-mono">
                  <span>Size: {(doc.file_size / 1024).toFixed(1)} KB</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
