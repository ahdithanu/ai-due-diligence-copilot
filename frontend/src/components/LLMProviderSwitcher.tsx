import React, { useState, useEffect } from 'react';
import { LLMSettings } from '../types';

export const LLMProviderSwitcher: React.FC = () => {
  const [settings, setSettings] = useState<LLMSettings | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>('mock');
  const [geminiKey, setGeminiKey] = useState<string>('');
  const [openaiKey, setOpenAIKey] = useState<string>('');
  const [showKeyModal, setShowKeyModal] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const fetchSettings = async () => {
    try {
      const res = await fetch('/api/v1/settings/llm');
      if (res.ok) {
        const data: LLMSettings = await res.json();
        setSettings(data);
        setSelectedProvider(data.current_provider);
      }
    } catch (e) {
      console.error('Failed to load LLM settings', e);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleProviderChange = async (newProvider: string) => {
    setSelectedProvider(newProvider);
    setIsSaving(true);
    try {
      const res = await fetch('/api/v1/settings/llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: newProvider }),
      });
      if (res.ok) {
        const updated: LLMSettings = await res.json();
        setSettings(updated);
        setSuccessBanner(`Provider switched to ${newProvider.toUpperCase()}`);
        setTimeout(() => setSuccessBanner(null), 3000);
      }
    } catch (e) {
      console.error('Failed to switch provider', e);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveKeys = async () => {
    setIsSaving(true);
    try {
      const payload: any = { provider: selectedProvider };
      if (geminiKey.trim()) payload.gemini_api_key = geminiKey.trim();
      if (openaiKey.trim()) payload.openai_api_key = openaiKey.trim();

      const res = await fetch('/api/v1/settings/llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const updated: LLMSettings = await res.json();
        setSettings(updated);
        setShowKeyModal(false);
        setGeminiKey('');
        setOpenAIKey('');
        setSuccessBanner('API Keys saved & live connection verified!');
        setTimeout(() => setSuccessBanner(null), 3000);
      }
    } catch (e) {
      console.error('Failed to save keys', e);
    } finally {
      setIsSaving(false);
    }
  };

  if (!settings) return null;

  return (
    <>
      <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-700/80 rounded-xl px-3 py-1.5 shadow-md text-xs">
        <span className="text-slate-400 font-mono text-[11px] uppercase tracking-wider flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${settings.is_live_ready ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
          Engine:
        </span>

        <select
          value={selectedProvider}
          onChange={(e) => handleProviderChange(e.target.value)}
          disabled={isSaving}
          aria-label="Active LLM Engine Provider"
          className="bg-slate-950 border border-slate-700 text-slate-200 font-semibold rounded-lg px-2.5 py-1 text-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
        >
          <option value="routed">Intelligent Router (Gemini + GPT-4o)</option>
          <option value="gemini">Google Gemini 1.5 Pro</option>
          <option value="openai">OpenAI GPT-4o</option>
          <option value="mock">Deterministic Mock (Test Mode)</option>
        </select>

        <button
          onClick={() => setShowKeyModal(true)}
          title="Configure API Keys"
          className="px-2 py-1 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-medium transition flex items-center gap-1 text-[11px]"
        >
          <span>🔑</span>
          <span>Keys</span>
          {settings.has_gemini_key || settings.has_openai_key ? (
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          ) : (
            <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
          )}
        </button>
      </div>

      {/* Success Notification Banner */}
      {successBanner && (
        <div className="fixed bottom-6 right-6 z-50 bg-emerald-950/90 border border-emerald-500 text-emerald-200 px-4 py-2.5 rounded-xl shadow-2xl text-xs font-semibold flex items-center gap-2 animate-bounce">
          <span>✅</span>
          <span>{successBanner}</span>
        </div>
      )}

      {/* API Key Modal */}
      {showKeyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="text-xl">🔐</span>
                <h3 className="font-bold text-white text-base">Configure Live LLM Credentials</h3>
              </div>
              <button
                onClick={() => setShowKeyModal(false)}
                className="text-slate-400 hover:text-white text-lg"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Connect live API keys to run real inference across data rooms. Keys are held in runtime memory and never committed to version control.
            </p>

            <div className="space-y-4 text-xs">
              {/* Google Gemini Key */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="font-semibold text-slate-300">Google Gemini API Key</label>
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${settings.has_gemini_key ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-slate-800 text-slate-400'}`}>
                    {settings.has_gemini_key ? '● Configured' : '○ Not Set'}
                  </span>
                </div>
                <input
                  type="password"
                  placeholder={settings.has_gemini_key ? '••••••••••••••••••••••••' : 'AIzaSy...'}
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              {/* OpenAI Key */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="font-semibold text-slate-300">OpenAI API Key</label>
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${settings.has_openai_key ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-slate-800 text-slate-400'}`}>
                    {settings.has_openai_key ? '● Configured' : '○ Not Set'}
                  </span>
                </div>
                <input
                  type="password"
                  placeholder={settings.has_openai_key ? '••••••••••••••••••••••••' : 'sk-proj-...'}
                  value={openaiKey}
                  onChange={(e) => setOpenAIKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800 text-xs">
              <button
                onClick={() => setShowKeyModal(false)}
                className="px-4 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveKeys}
                disabled={isSaving}
                className="px-5 py-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white font-bold shadow-lg shadow-indigo-500/20 disabled:opacity-50"
              >
                {isSaving ? 'Connecting...' : 'Save & Verify'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
