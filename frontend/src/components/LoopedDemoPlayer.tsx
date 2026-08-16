import React, { useState, useEffect, useRef } from 'react';
import { DemoStatusResponse } from '../types';

interface LoopedDemoPlayerProps {
  onTabChange?: (tab: string) => void;
}

export const LoopedDemoPlayer: React.FC<LoopedDemoPlayerProps> = ({ onTabChange }) => {
  const [demoStatus, setDemoStatus] = useState<DemoStatusResponse | null>(null);
  const [speed, setSpeed] = useState<number>(1.0);
  const [autoLoop, setAutoLoop] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const lastActiveTabRef = useRef<string | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/v1/demo/status');
      if (res.ok) {
        const data: DemoStatusResponse = await res.json();
        setDemoStatus(data);
        setSpeed(data.speed);
        setAutoLoop(data.auto_loop);

        // Auto tab switcher sync
        if (data.active && data.active_tab && data.active_tab !== lastActiveTabRef.current) {
          lastActiveTabRef.current = data.active_tab;
          if (onTabChange) {
            onTabChange(data.active_tab);
          }
        }
      }
    } catch (err) {
      console.error('Failed to poll demo status', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(() => {
      fetchStatus();
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  const handlePlay = async () => {
    setLoading(true);
    try {
      const endpoint = demoStatus?.active && demoStatus?.paused ? '/api/v1/demo/resume' : '/api/v1/demo/start';
      const body = endpoint === '/api/v1/demo/start' ? JSON.stringify({ speed, loop: autoLoop }) : undefined;
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body
      });
      if (res.ok) {
        const data = await res.json();
        setDemoStatus(data);
        if (data.active_tab && onTabChange) {
          lastActiveTabRef.current = data.active_tab;
          onTabChange(data.active_tab);
        }
      }
    } catch (err) {
      console.error('Failed to start/resume demo', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/demo/pause', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setDemoStatus(data);
      }
    } catch (err) {
      console.error('Failed to pause demo', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStep = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/demo/step', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setDemoStatus(data);
        if (data.active_tab && onTabChange) {
          lastActiveTabRef.current = data.active_tab;
          onTabChange(data.active_tab);
        }
      }
    } catch (err) {
      console.error('Failed to step demo', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/demo/reset', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setDemoStatus(data);
        lastActiveTabRef.current = null;
      }
    } catch (err) {
      console.error('Failed to reset demo', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSpeedChange = async (newSpeed: number) => {
    setSpeed(newSpeed);
    if (demoStatus?.active) {
      try {
        const res = await fetch('/api/v1/demo/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ speed: newSpeed, loop: autoLoop })
        });
        if (res.ok) {
          const data = await res.json();
          setDemoStatus(data);
        }
      } catch (err) {
        console.error('Failed to set demo speed', err);
      }
    }
  };

  const handleLoopToggle = async () => {
    const newLoop = !autoLoop;
    setAutoLoop(newLoop);
    if (demoStatus?.active) {
      try {
        const res = await fetch('/api/v1/demo/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ speed, loop: newLoop })
        });
        if (res.ok) {
          const data = await res.json();
          setDemoStatus(data);
        }
      } catch (err) {
        console.error('Failed to toggle demo loop', err);
      }
    }
  };

  const isActive = demoStatus?.active;
  const isPaused = demoStatus?.paused;

  return (
    <div className="bg-slate-950/90 border-b border-indigo-500/30 backdrop-blur-md px-4 py-2 text-xs flex flex-wrap items-center justify-between gap-3 shadow-md shadow-indigo-950/30 sticky top-0 z-50">
      {/* Live Demo Status Badge */}
      <div className="flex items-center gap-3">
        {isActive && !isPaused ? (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950/90 text-emerald-300 border border-emerald-500/50 font-bold tracking-wide shadow-sm shadow-emerald-900/40">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
            </span>
            🟢 DEMO AUTO-PLAYING
          </span>
        ) : isActive && isPaused ? (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-950/90 text-amber-300 border border-amber-500/50 font-bold tracking-wide">
            ⏸️ DEMO PAUSED
          </span>
        ) : (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 text-slate-400 border border-slate-800 font-semibold">
            ⏹️ MANUAL MODE
          </span>
        )}

        {/* Step Name & Progress Tracker */}
        <div className="hidden lg:flex items-center gap-3 border-l border-slate-800 pl-3">
          <span className="font-semibold text-slate-200 truncate max-w-xs">
            {demoStatus?.current_step_name || '1. Deployment Selection & Profile Configuration'}
          </span>
          {demoStatus?.loop_count ? (
            <span className="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 font-mono text-[10px] border border-indigo-800">
              Loop #{demoStatus.loop_count}
            </span>
          ) : null}
        </div>
      </div>

      {/* Progress Bar & Numerical Indicator */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-2">
          <div className="w-28 bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 h-full transition-all duration-500"
              style={{ width: `${demoStatus?.progress_pct || 0}%` }}
            />
          </div>
          <span className="font-mono text-[11px] text-slate-400 min-w-[36px]">
            {Math.round(demoStatus?.progress_pct || 0)}%
          </span>
        </div>

        {/* Controls: Play, Pause, Step, Reset */}
        <div className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
          {isActive && !isPaused ? (
            <button
              onClick={handlePause}
              disabled={loading}
              title="Pause Demo"
              className="px-2.5 py-1 rounded-lg bg-amber-600/30 hover:bg-amber-600/50 text-amber-200 font-bold transition-all border border-amber-500/40 active:scale-95"
            >
              ⏸️ Pause
            </button>
          ) : (
            <button
              onClick={handlePlay}
              disabled={loading}
              title="Play Demo"
              className="px-2.5 py-1 rounded-lg bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-200 font-bold transition-all border border-emerald-500/40 active:scale-95 flex items-center gap-1"
            >
              <span>▶️</span> {isPaused ? 'Resume' : 'Play'}
            </button>
          )}

          <button
            onClick={handleStep}
            disabled={loading}
            title="Step Forward"
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold transition-all border border-slate-700 active:scale-95"
          >
            ⏭️ Step
          </button>

          <button
            onClick={handleReset}
            disabled={loading}
            title="Reset Demo"
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold transition-all border border-slate-700 active:scale-95"
          >
            🔄 Reset
          </button>
        </div>

        {/* Speed Selector */}
        <div className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
          {[1.0, 2.0, 5.0].map((s) => (
            <button
              key={s}
              onClick={() => handleSpeedChange(s)}
              className={`px-2 py-0.5 rounded-md text-[11px] font-bold font-mono transition-all ${
                speed === s
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>

        {/* Auto-Loop Toggle */}
        <button
          onClick={handleLoopToggle}
          className={`px-2.5 py-1 rounded-xl text-[11px] font-bold transition-all border flex items-center gap-1 ${
            autoLoop
              ? 'bg-indigo-950/80 text-indigo-300 border-indigo-700 shadow-sm'
              : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-slate-300'
          }`}
        >
          <span>🔄</span> {autoLoop ? 'Loop On' : 'Loop Off'}
        </button>
      </div>
    </div>
  );
};
