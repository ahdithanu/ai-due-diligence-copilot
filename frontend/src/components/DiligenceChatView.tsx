import React, { useState } from 'react';
import { ChatMessage, Citation, DataRoomRequest } from '../types';

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: 'msg-1',
    sender: 'system',
    text: 'Welcome to the Diligence Intelligence Assistant. Ask any question grounded in the data room documents, financial metrics, term sheets, or risk register.',
    timestamp: '10:00 AM',
  },
  {
    id: 'msg-2',
    sender: 'user',
    text: 'What is the liquidation preference stack and are there any participating preferred rights?',
    timestamp: '10:01 AM',
  },
  {
    id: 'msg-3',
    sender: 'assistant',
    text: 'Based on the Series B Restated Certificate of Incorporation and Term Sheet, the company has a 1.0x non-participating liquidation preference stack with Series B holding Seniority Rank #1, followed by Series A (Rank #2), and Seed Preferred (Rank #3).\n\nKey clauses verified:\n1. Series B holds Senior Preference to Series A & Seed (1.0x payout).\n2. Preferred shares are Non-Participating; holders convert to Common if common pro-rata proceeds exceed preference payout.\n3. There is no cumulative dividend feature.',
    timestamp: '10:01 AM',
    citations: [
      {
        source_id: 'doc-term-sheet-01',
        document_name: 'Series_B_Restated_CoI.pdf',
        page_number: 14,
        section_title: 'Section 4.2 Liquidation Preference',
        snippet: 'In the event of any Liquidation Event, Series B Preferred shall be entitled to receive $1.00 per share plus declared dividends prior to any distribution to Series A or Common.',
        relevance_score: 0.98,
        claim_type: 'FACT',
      },
      {
        source_id: 'doc-cap-table-02',
        document_name: 'Audit_CapTable_Q2_2026.xlsx',
        page_number: 2,
        section_title: 'Ownership Summary',
        snippet: 'Series B Preferred: 2,500,000 shares ($15,000,000 invested capital). Non-participating.',
        relevance_score: 0.95,
        claim_type: 'CALCULATION',
      },
    ],
    suggested_followups: [
      'What is the common payout at $100M exit valuation?',
      'Request full cap table pro-forma for Series B',
      'Are there any anti-dilution ratchet clauses?',
    ],
  },
  {
    id: 'msg-4',
    sender: 'user',
    text: 'Are there any customer concentration risks >10% of ARR?',
    timestamp: '10:03 AM',
  },
  {
    id: 'msg-5',
    sender: 'assistant',
    text: 'Yes. Customer Concentration audit reveals 1 critical concentration risk:\n• Customer Alpha Corp accounts for 18.2% of total ARR ($1.53M ARR out of $8.40M total ARR).\n• The contract renewal is scheduled for Q4 2026 with an opt-out clause.\n\nNo other single customer accounts for more than 7.5% of total ARR.',
    timestamp: '10:03 AM',
    citations: [
      {
        source_id: 'doc-arr-ledger',
        document_name: 'ARR_Customer_Cohort_Ledger_2026.xlsx',
        page_number: 5,
        section_title: 'Top 10 Accounts Breakdown',
        snippet: 'Customer Alpha Corp: $1,528,800 ARR (18.2% of total ARR). Renewal Date: Nov 30, 2026.',
        relevance_score: 0.96,
        claim_type: 'FACT',
      },
    ],
    suggested_followups: [
      'Create Data Room Request for Alpha Corp contract',
      'Show NRR retention excluding Alpha Corp',
    ],
  },
];

const INITIAL_REQUESTS: DataRoomRequest[] = [
  {
    id: 'dr-1',
    title: 'Customer Alpha Corp Master Services Agreement & Opt-out Terms',
    category: 'Customer',
    priority: 'HIGH',
    status: 'OPEN',
    requested_by: 'Investment Committee',
    reason_it_matters: 'Alpha Corp represents 18.2% of total ARR with upcoming Q4 renewal',
    created_at: 'Aug 12, 2026',
  },
  {
    id: 'dr-2',
    title: 'SOC2 Type II Audit Report & Pen Test Executive Summary',
    category: 'Technical',
    priority: 'MEDIUM',
    status: 'IN_PROGRESS',
    requested_by: 'CTO Due Diligence Team',
    reason_it_matters: 'Verify enterprise security compliance for financial sector deployments',
    created_at: 'Aug 11, 2026',
  },
  {
    id: 'dr-3',
    title: 'Audited Financial Statements FY2024 & FY2025',
    category: 'Financials',
    priority: 'HIGH',
    status: 'FULFILLED',
    requested_by: 'VP Finance',
    reason_it_matters: 'Reconcile historical revenue recognition with tax filings',
    created_at: 'Aug 09, 2026',
  },
];

export const DiligenceChatView: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [inputText, setInputText] = useState<string>('');
  const [dataRoomRequests, setDataRoomRequests] = useState<DataRoomRequest[]>(INITIAL_REQUESTS);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  // New Data Room Request Modal / Form state
  const [showAddRequestModal, setShowAddRequestModal] = useState<boolean>(false);
  const [newReqTitle, setNewReqTitle] = useState<string>('');
  const [newReqCategory, setNewReqCategory] = useState<string>('Financials');
  const [newReqPriority, setNewReqPriority] = useState<'HIGH' | 'MEDIUM' | 'LOW'>('HIGH');
  const [newReqReason, setNewReqReason] = useState<string>('');

  const handleSendMessage = (textToSend?: string) => {
    const query = textToSend || inputText;
    if (!query.trim()) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputText('');

    // Generate Evidence-Grounded AI Response
    setTimeout(() => {
      let aiText = `Analysis regarding "${query}":\n\nCross-referencing data room index across financial records, legal filings, and technical architecture docs:\n• Verified 100% agreement between ledger records and term sheet representations.\n• No undisclosed liabilities or litigation flags were identified in background searches.`;
      let citations: Citation[] = [
        {
          source_id: 'doc-gen-01',
          document_name: 'Diligence_Master_Index.pdf',
          page_number: 8,
          section_title: 'Executive Legal Audit',
          snippet: 'All corporate filings and board resolutions reconciled cleanly with cap table records.',
          relevance_score: 0.94,
          claim_type: 'FACT',
        },
      ];

      if (query.toLowerCase().includes('nrr') || query.toLowerCase().includes('retention')) {
        aiText = `Net Revenue Retention (NRR) Analysis:\n• Current NRR: 118.4% YoY across enterprise cohorts.\n• Gross Dollar Retention (GDR): 94.2%.\n• Main Expansion Driver: Seat expansion & API usage tiers (+24% expansion ARR).`;
        citations = [
          {
            source_id: 'doc-cohort',
            document_name: 'SaaS_Cohort_Retention_Q2.xlsx',
            page_number: 3,
            section_title: 'Enterprise Cohort Retention',
            snippet: '2024 Cohort expanded from $2.1M to $2.55M ARR (+21.4% expansion).',
            relevance_score: 0.97,
            claim_type: 'CALCULATION',
          },
        ];
      }

      const aiMsg: ChatMessage = {
        id: `msg-ai-${Date.now()}`,
        sender: 'assistant',
        text: aiText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations,
        suggested_followups: [
          'Request detailed cohort expansion breakdown',
          'Add Data Room request for top churn reasons',
        ],
      };

      setMessages((prev) => [...prev, aiMsg]);
    }, 600);
  };

  const handleToggleRequestStatus = (id: string) => {
    setDataRoomRequests((prev) =>
      prev.map((req) => {
        if (req.id !== id) return req;
        const nextStatus: Record<string, 'OPEN' | 'IN_PROGRESS' | 'FULFILLED'> = {
          OPEN: 'IN_PROGRESS',
          IN_PROGRESS: 'FULFILLED',
          FULFILLED: 'OPEN',
        };
        return { ...req, status: nextStatus[req.status] || 'OPEN' };
      })
    );
  };

  const handleCreateDataRoomRequest = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newReqTitle.trim()) return;

    const newReq: DataRoomRequest = {
      id: `dr-${Date.now()}`,
      title: newReqTitle,
      category: newReqCategory,
      priority: newReqPriority,
      status: 'OPEN',
      requested_by: 'Due Diligence Associate',
      reason_it_matters: newReqReason || 'Required for complete institutional audit',
      created_at: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    };

    setDataRoomRequests((prev) => [newReq, ...prev]);
    setNewReqTitle('');
    setNewReqReason('');
    setShowAddRequestModal(false);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">💬</span>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Evidence-Grounded Diligence Chatbot
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30">
              100% Citation Grounded
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Query investment documents, financial models, and term sheets with interactive page-level citation popovers &amp; automated Data Room Request generation.
          </p>
        </div>

        <button
          onClick={() => setShowAddRequestModal(true)}
          className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md transition-all border border-indigo-500"
        >
          + New Data Room Request
        </button>
      </div>

      {/* Main Grid: Chat Stream (Left) vs Data Room Requests Manager (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Stream Window */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col h-[640px]">
          {/* Chat Header */}
          <div className="pb-4 mb-4 border-b border-slate-800/80 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-xs font-bold text-slate-200">Diligence Knowledge Engine</span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">
              {messages.filter((m) => m.sender === 'assistant').length} Answers Grounded
            </span>
          </div>

          {/* Message List */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {messages.map((msg) => {
              const isUser = msg.sender === 'user';
              const isSystem = msg.sender === 'system';

              if (isSystem) {
                return (
                  <div key={msg.id} className="text-center py-2">
                    <span className="px-3 py-1.5 rounded-xl text-[11px] bg-slate-900 text-slate-400 border border-slate-800 inline-block">
                      {msg.text}
                    </span>
                  </div>
                );
              }

              return (
                <div
                  key={msg.id}
                  className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1.5`}
                >
                  <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono">
                    <span>{isUser ? 'You (Partner)' : '🤖 AI Copilot'}</span>
                    <span>•</span>
                    <span>{msg.timestamp}</span>
                  </div>

                  <div
                    className={`max-w-[88%] p-4 rounded-2xl text-xs leading-relaxed whitespace-pre-wrap ${
                      isUser
                        ? 'bg-indigo-600 text-white rounded-tr-none shadow-md'
                        : 'bg-slate-900/90 text-slate-200 border border-slate-800 rounded-tl-none space-y-3'
                    }`}
                  >
                    <div>{msg.text}</div>

                    {/* Citations Badges */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="pt-3 border-t border-slate-800/80 space-y-1.5">
                        <span className="text-[10px] uppercase font-mono tracking-wider text-teal-400 font-bold block">
                          Verified Document Sources:
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {msg.citations.map((cite) => (
                            <button
                              key={cite.source_id}
                              onClick={() => setActiveCitation(cite)}
                              className="px-2.5 py-1 rounded-lg text-[10px] font-mono bg-teal-950/80 hover:bg-teal-900 border border-teal-500/40 text-teal-300 transition-colors flex items-center gap-1.5 shadow-sm"
                            >
                              <span>📄</span>
                              <span>{cite.document_name}</span>
                              <span className="text-teal-400/70">(p.{cite.page_number})</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Suggested Followups */}
                    {msg.suggested_followups && (
                      <div className="pt-2 flex flex-wrap gap-1.5">
                        {msg.suggested_followups.map((prompt, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSendMessage(prompt)}
                            className="px-2.5 py-1 rounded-lg text-[10px] bg-slate-800/80 hover:bg-slate-800 text-indigo-300 border border-indigo-500/20 transition-colors"
                          >
                            &rarr; {prompt}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Input Box */}
          <div className="pt-4 mt-2 border-t border-slate-800/80 space-y-2">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask about liquidation prefs, customer concentration, NRR retention..."
                className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
              />
              <button
                onClick={() => handleSendMessage()}
                className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-md"
              >
                Send &rarr;
              </button>
            </div>

            {/* Quick Starters */}
            <div className="flex flex-wrap gap-1.5 text-[10px]">
              <span className="text-slate-500 font-semibold">Quick Prompts:</span>
              {[
                'Liquidation preference stack?',
                'Customer concentration risks?',
                'IP ownership audit',
                'NRR & CAC payback trend',
              ].map((p) => (
                <button
                  key={p}
                  onClick={() => handleSendMessage(p)}
                  className="text-slate-400 hover:text-white underline decoration-slate-700"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Data Room Request List Manager Panel */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col justify-between space-y-4">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span>📁</span> Data Room Request List
              </h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                {dataRoomRequests.filter((r) => r.status === 'OPEN').length} Open Requests
              </span>
            </div>

            <p className="text-xs text-slate-400">
              Track outstanding information requests required from founder / target executive team before IC vote.
            </p>

            <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
              {dataRoomRequests.map((req) => {
                const statusBadge =
                  req.status === 'FULFILLED'
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                    : req.status === 'IN_PROGRESS'
                    ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
                    : 'bg-amber-500/20 text-amber-400 border-amber-500/30';

                return (
                  <div
                    key={req.id}
                    className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex justify-between items-start">
                      <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-slate-800 text-slate-300 font-mono">
                        {req.category}
                      </span>

                      <button
                        onClick={() => handleToggleRequestStatus(req.id)}
                        className={`px-2 py-0.5 rounded text-[9px] font-extrabold border transition-all ${statusBadge}`}
                      >
                        {req.status} (click to change)
                      </button>
                    </div>

                    <h4 className="text-xs font-bold text-white leading-snug">{req.title}</h4>

                    <p className="text-[11px] text-slate-400 leading-relaxed">
                      💡 <strong>Why it matters:</strong> {req.reason_it_matters}
                    </p>

                    <div className="flex justify-between items-center text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-800/60">
                      <span>By: {req.requested_by}</span>
                      <span>{req.created_at}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Citation Popover Modal */}
      {activeCitation && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel p-6 rounded-2xl border border-teal-500/40 max-w-lg w-full bg-slate-900 space-y-4 shadow-2xl">
            <div className="flex justify-between items-start">
              <div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-500/20 text-teal-300 border border-teal-500/30 font-mono">
                  {activeCitation.claim_type || 'VERIFIED EVIDENCE'}
                </span>
                <h3 className="text-base font-bold text-white mt-1">
                  {activeCitation.document_name}
                </h3>
              </div>
              <button
                onClick={() => setActiveCitation(null)}
                className="text-slate-400 hover:text-white text-lg font-bold px-2"
              >
                ✕
              </button>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono text-slate-300 space-y-2">
              <div className="flex justify-between text-slate-400 text-[10px]">
                <span>Section: {activeCitation.section_title || 'N/A'}</span>
                <span>Page {activeCitation.page_number}</span>
              </div>
              <p className="italic text-teal-200/90 leading-relaxed">
                "{activeCitation.snippet}"
              </p>
            </div>

            <div className="flex justify-between items-center text-xs text-slate-400">
              <span>Relevance Score: <strong>{(activeCitation.relevance_score * 100).toFixed(0)}%</strong></span>
              <button
                onClick={() => setActiveCitation(null)}
                className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold transition-colors"
              >
                Close Popover
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Data Room Request Modal */}
      {showAddRequestModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleCreateDataRoomRequest}
            className="glass-panel p-6 rounded-2xl border border-indigo-500/40 max-w-md w-full bg-slate-900 space-y-4 shadow-2xl"
          >
            <div className="flex justify-between items-center">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>📁</span> Add Data Room Request
              </h3>
              <button
                type="button"
                onClick={() => setShowAddRequestModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 font-bold block mb-1">Request Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Audited FY25 Revenue Reconciliation Sheet"
                  value={newReqTitle}
                  onChange={(e) => setNewReqTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-bold block mb-1">Category</label>
                  <select
                    value={newReqCategory}
                    onChange={(e) => setNewReqCategory(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                  >
                    <option value="Financials">Financials</option>
                    <option value="Legal">Legal</option>
                    <option value="Technical">Technical</option>
                    <option value="Customer">Customer</option>
                    <option value="Compliance">Compliance</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-300 font-bold block mb-1">Priority</label>
                  <select
                    value={newReqPriority}
                    onChange={(e) => setNewReqPriority(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                  >
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-300 font-bold block mb-1">Why It Matters (Reason)</label>
                <textarea
                  rows={3}
                  placeholder="Explain why this item is essential for IC thesis verification..."
                  value={newReqReason}
                  onChange={(e) => setNewReqReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowAddRequestModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold"
              >
                Add Request
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
