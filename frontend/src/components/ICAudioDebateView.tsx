import React, { useState, useEffect, useRef } from 'react';
import { ICAudioScript, ICAudioTurn } from '../types';

const MOCK_DEBATE_SCRIPT: ICAudioScript = {
  id: 'ic-audio-001',
  title: 'Investment Committee Final Debate: Series B Lead Investment',
  total_duration_sec: 140,
  summary: 'Partners debate market size, customer concentration risks, CAC payback efficiency, and valuation cap before taking final IC consensus vote.',
  speakers: [
    {
      role: 'Bull',
      name: 'Alex Rivera',
      avatar_color: 'green',
      title: 'Managing Partner (Growth Lead)',
    },
    {
      role: 'Bear',
      name: 'Marcus Vance',
      avatar_color: 'red',
      title: 'Senior Partner (Risk & Valuation)',
    },
    {
      role: 'Skeptic',
      name: 'Dr. Elena Rostova',
      avatar_color: 'yellow',
      title: 'General Partner (Technical & IP Audit)',
    },
  ],
  turns: [
    {
      id: 'turn-1',
      speaker: 'Bull',
      speaker_name: 'Alex Rivera',
      avatar_color: 'green',
      start_time_sec: 0,
      end_time_sec: 25,
      text: 'Team, I want to kick off the IC debate for our proposed $15M Series B lead check. The core growth thesis is clear: ARR has scaled 2.4x YoY to $8.4M, with 118% net revenue retention across enterprise accounts. Their AI diligence graph engine creates an unbeatable product moat.',
      key_point: 'Growth thesis: 2.4x YoY ARR expansion to $8.4M with 118% NRR moat',
      sentiment: 'positive',
    },
    {
      id: 'turn-2',
      speaker: 'Bear',
      speaker_name: 'Marcus Vance',
      avatar_color: 'red',
      start_time_sec: 25,
      end_time_sec: 55,
      text: 'Alex, I acknowledge the top-line growth, but we cannot ignore the concentration risk and valuation inflation. Customer Alpha Corp accounts for 18.2% of total ARR and their renewal opt-out is in Q4. Asking for a $60M post-money valuation with only 14 months of runway leaves zero safety margin if Alpha Corp churns.',
      key_point: 'Risk thesis: 18.2% ARR customer concentration & high $60M valuation cap',
      sentiment: 'negative',
    },
    {
      id: 'turn-3',
      speaker: 'Skeptic',
      speaker_name: 'Dr. Elena Rostova',
      avatar_color: 'yellow',
      start_time_sec: 55,
      end_time_sec: 85,
      text: 'I conducted the technical audit on their LLM graph extraction pipeline. The deterministic verification node operates with 99.4% accuracy, which is genuinely state-of-the-art. However, they lack SOC2 Type II certification, which could stall their enterprise pipeline in banking.',
      key_point: 'Technical audit: 99.4% graph extraction accuracy, but missing SOC2 Type II certification',
      sentiment: 'neutral',
    },
    {
      id: 'turn-4',
      speaker: 'Bull',
      speaker_name: 'Alex Rivera',
      avatar_color: 'green',
      start_time_sec: 85,
      end_time_sec: 110,
      text: 'We can structure a milestone-gated check: release $10M initially, with $5M contingent on securing SOC2 compliance and executing the Alpha Corp 2-year renewal contract. This mitigates Marcus\'s downside concern completely.',
      key_point: 'Mitigation structure: Tranche $15M check ($10M upfront + $5M on SOC2/Alpha Corp renewal)',
      sentiment: 'positive',
    },
    {
      id: 'turn-5',
      speaker: 'Bear',
      speaker_name: 'Marcus Vance',
      avatar_color: 'red',
      start_time_sec: 110,
      end_time_sec: 140,
      text: 'If we cap valuation at $50M post-money and enforce the tranche milestone structure, I will switch my vote from Pass to Conditional Invest. Let\'s put it to a vote.',
      key_point: 'Consensus reached: Conditional Invest at $50M post-money with milestone tranches',
      sentiment: 'neutral',
    },
  ],
};

export const ICAudioDebateView: React.FC = () => {
  const script = MOCK_DEBATE_SCRIPT;
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTimeSec, setCurrentTimeSec] = useState<number>(0);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Sync Timer for Audio Simulation
  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        setCurrentTimeSec((prev) => {
          if (prev >= script.total_duration_sec) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 1000 / playbackSpeed);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, playbackSpeed, script.total_duration_sec]);

  // Find active turn based on current time
  const activeTurn = script.turns.find(
    (turn) => currentTimeSec >= turn.start_time_sec && currentTimeSec <= turn.end_time_sec
  ) || script.turns[0];

  const handleSeek = (sec: number) => {
    setCurrentTimeSec(Math.min(Math.max(0, sec), script.total_duration_sec));
  };

  const formatTime = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = Math.floor(totalSec % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const getAvatarBadge = (role: 'Bull' | 'Bear' | 'Skeptic') => {
    if (role === 'Bull') return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
    if (role === 'Bear') return 'bg-rose-500/20 text-rose-400 border-rose-500/40';
    return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">🎧</span>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Investment Committee Audio Debate Synthesizer
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Multi-Partner Debate Simulation
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Listen to synthesized IC debate between Bull (Growth), Bear (Risk/Valuation), and Skeptic (Tech/IP) partners with live transcript tracking.
          </p>
        </div>

        {/* IC Vote Summary Pill */}
        <div className="flex items-center gap-2 bg-slate-900 p-2.5 rounded-xl border border-slate-800 text-xs">
          <span className="font-semibold text-slate-400">Vote Consensus:</span>
          <span className="px-2.5 py-1 rounded-lg font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            CONDITIONAL INVEST ($50M Cap)
          </span>
        </div>
      </div>

      {/* Partner Avatars Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {script.speakers.map((speaker) => {
          const isSpeakingNow = activeTurn.speaker === speaker.role && isPlaying;
          const avatarBorder =
            speaker.role === 'Bull'
              ? 'border-emerald-500/50'
              : speaker.role === 'Bear'
              ? 'border-rose-500/50'
              : 'border-amber-500/50';

          return (
            <div
              key={speaker.role}
              className={`p-4 rounded-2xl bg-slate-900/80 border transition-all ${avatarBorder} ${
                isSpeakingNow ? 'ring-2 ring-indigo-400 scale-[1.02] shadow-xl' : 'opacity-85'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center font-black text-base border ${
                    speaker.role === 'Bull'
                      ? 'bg-emerald-950 text-emerald-300 border-emerald-500'
                      : speaker.role === 'Bear'
                      ? 'bg-rose-950 text-rose-300 border-rose-500'
                      : 'bg-amber-950 text-amber-300 border-amber-500'
                  }`}
                >
                  {speaker.role === 'Bull' ? '🐂' : speaker.role === 'Bear' ? '🐻' : '🧐'}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-white">{speaker.name}</h3>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold border ${getAvatarBadge(speaker.role)}`}>
                      {speaker.role}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">{speaker.title}</p>
                </div>
              </div>

              {isSpeakingNow && (
                <div className="mt-3 pt-2 border-t border-slate-800 flex items-center gap-2 text-[10px] font-mono text-indigo-300 animate-pulse">
                  <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                  <span>Speaking now...</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Audio Player Control Bar */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            {/* Play/Pause Button */}
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="w-12 h-12 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center text-xl shadow-lg transition-transform active:scale-95"
            >
              {isPlaying ? '⏸' : '▶'}
            </button>

            {/* Skip Controls */}
            <button
              onClick={() => handleSeek(currentTimeSec - 10)}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white border border-slate-700"
            >
              ⏪ 10s
            </button>
            <button
              onClick={() => handleSeek(currentTimeSec + 10)}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white border border-slate-700"
            >
              10s ⏩
            </button>

            <span className="text-xs font-mono font-extrabold text-white pl-2">
              {formatTime(currentTimeSec)} / {formatTime(script.total_duration_sec)}
            </span>
          </div>

          {/* Speed Selector */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400 font-semibold">Speed:</span>
            {[1.0, 1.25, 1.5, 2.0].map((spd) => (
              <button
                key={spd}
                onClick={() => setPlaybackSpeed(spd)}
                className={`px-2.5 py-1 rounded-lg font-mono font-bold transition-all border ${
                  playbackSpeed === spd
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-md'
                    : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-white'
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>

        {/* Scrubber Progress Bar */}
        <div className="space-y-1">
          <input
            type="range"
            min={0}
            max={script.total_duration_sec}
            value={currentTimeSec}
            onChange={(e) => handleSeek(Number(e.target.value))}
            className="w-full h-2.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
          <div className="flex justify-between text-[10px] font-mono text-slate-500">
            <span>0:00 (Growth Thesis)</span>
            <span>0:55 (Tech Audit)</span>
            <span>2:20 (Consensus Vote)</span>
          </div>
        </div>
      </div>

      {/* Transcript Highlighter Section */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <span>📜</span> Synchronized Transcript Tracker (Click any line to jump audio)
        </h3>

        <div className="space-y-3">
          {script.turns.map((turn) => {
            const isActive = activeTurn.id === turn.id;

            return (
              <div
                key={turn.id}
                onClick={() => {
                  handleSeek(turn.start_time_sec);
                  setIsPlaying(true);
                }}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  isActive
                    ? 'bg-indigo-950/70 border-indigo-500 text-white ring-1 ring-indigo-500 shadow-lg'
                    : 'bg-slate-900/60 border-slate-800/80 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-extrabold border ${getAvatarBadge(turn.speaker)}`}>
                      {turn.speaker} ({turn.speaker_name})
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      [{formatTime(turn.start_time_sec)} - {formatTime(turn.end_time_sec)}]
                    </span>
                  </div>

                  {isActive && (
                    <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-indigo-500 text-white animate-pulse">
                      PLAYING NOW
                    </span>
                  )}
                </div>

                <p className="text-xs leading-relaxed font-sans">{turn.text}</p>

                {turn.key_point && (
                  <div className="mt-2 pt-2 border-t border-slate-800/60 text-[11px] font-mono text-indigo-300 flex items-center gap-1.5">
                    <span>💡</span>
                    <span><strong>Key Argument:</strong> {turn.key_point}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
