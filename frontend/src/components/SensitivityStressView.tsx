import React, { useState, useMemo } from 'react';
import { SensitivityMatrixCell } from '../types';

interface StressScenarioPreset {
  id: string;
  name: string;
  description: string;
  burnShiftPct: number;
  growthShiftPct: number;
  icon: string;
  severityTag: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

const PRESET_SCENARIOS: StressScenarioPreset[] = [
  {
    id: 'base',
    name: 'Base Case Plan',
    description: 'Current baseline projections without market shocks',
    burnShiftPct: 0,
    growthShiftPct: 0,
    icon: '🎯',
    severityTag: 'LOW',
  },
  {
    id: 'churn_spike',
    name: 'Customer Churn Spike (+25%)',
    description: 'NPS drops, key enterprise customer churn increases monthly burn',
    burnShiftPct: 25,
    growthShiftPct: -20,
    icon: '🔻',
    severityTag: 'HIGH',
  },
  {
    id: 'sales_cycle_doubled',
    name: 'Sales Cycle Doubled',
    description: 'Enterprise procurement delays push bookings out by 2 quarters',
    burnShiftPct: 15,
    growthShiftPct: -35,
    icon: 'CRITICAL',
    severityTag: 'CRITICAL',
  },
  {
    id: 'cac_inflation',
    name: 'CAC Inflation (+40%)',
    description: 'Paid acquiring channels degrade in efficiency while hiring continues',
    burnShiftPct: 30,
    growthShiftPct: -10,
    icon: '📈',
    severityTag: 'HIGH',
  },
  {
    id: 'cost_cut_mitigation',
    name: 'Emergency RIF / Cost Cut',
    description: 'Freeze hiring & cut marketing spend by 25% to stretch runway',
    burnShiftPct: -25,
    growthShiftPct: -10,
    icon: '🛡️',
    severityTag: 'LOW',
  },
];

const BURN_STEPS = [-30, -15, 0, 15, 30];
const GROWTH_STEPS = [-30, -15, 0, 15, 30];

export const SensitivityStressView: React.FC = () => {
  // Baseline financial metrics
  const [baseCashUsd] = useState<number>(12500000); // $12.5M
  const [baseBurnUsd] = useState<number>(680000); // $680k/mo

  // Active shifts
  const [activeBurnShift, setActiveBurnShift] = useState<number>(0);
  const [activeGrowthShift, setActiveGrowthShift] = useState<number>(0);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('base');

  const formatShift = (val: number) => {
    return val >= 0 ? `+${val}%` : `${val}%`;
  };

  // Calculate Base Runway
  const baseRunwayMonths = useMemo(() => {
    return baseBurnUsd > 0 ? baseCashUsd / baseBurnUsd : 99;
  }, [baseCashUsd, baseBurnUsd]);

  // Calculate Stressed Runway
  const stressedRunway = useMemo(() => {
    const effectiveBurn = baseBurnUsd * (1 + activeBurnShift / 100);
    const effectiveArrGrowth = 45 * (1 + activeGrowthShift / 100); // 45% base ARR growth
    const months = effectiveBurn > 0 ? baseCashUsd / effectiveBurn : 99;
    const compressionPct = ((baseRunwayMonths - months) / baseRunwayMonths) * 100;

    let alertLevel: 'HEALTHY' | 'MODERATE' | 'CRITICAL' = 'HEALTHY';
    if (months < 10) alertLevel = 'CRITICAL';
    else if (months < 15) alertLevel = 'MODERATE';

    return {
      effectiveBurn,
      effectiveArrGrowth,
      months,
      compressionPct,
      alertLevel,
    };
  }, [baseCashUsd, baseBurnUsd, activeBurnShift, activeGrowthShift, baseRunwayMonths]);

  // Build 5x5 Matrix
  const matrixData = useMemo(() => {
    const grid: SensitivityMatrixCell[][] = [];

    for (let r = 0; r < BURN_STEPS.length; r++) {
      const row: SensitivityMatrixCell[] = [];
      const burnDelta = BURN_STEPS[r];

      for (let c = 0; c < GROWTH_STEPS.length; c++) {
        const growthDelta = GROWTH_STEPS[c];
        const effBurn = baseBurnUsd * (1 + burnDelta / 100);
        const effGrowth = 45 * (1 + growthDelta / 100);
        const runway = effBurn > 0 ? baseCashUsd / effBurn : 99;
        const compPct = ((baseRunwayMonths - runway) / baseRunwayMonths) * 100;

        let alert: 'HEALTHY' | 'MODERATE' | 'CRITICAL' = 'HEALTHY';
        if (runway < 10) alert = 'CRITICAL';
        else if (runway < 15) alert = 'MODERATE';

        row.push({
          burn_delta_pct: burnDelta,
          growth_delta_pct: growthDelta,
          effective_burn_usd: effBurn,
          effective_arr_growth_pct: effGrowth,
          runway_months: Number(runway.toFixed(1)),
          runway_compression_pct: Number(compPct.toFixed(1)),
          alert_level: alert,
        });
      }
      grid.push(row);
    }
    return grid;
  }, [baseCashUsd, baseBurnUsd, baseRunwayMonths]);

  const handleSelectScenario = (scenario: StressScenarioPreset) => {
    setSelectedScenarioId(scenario.id);
    setActiveBurnShift(scenario.burnShiftPct);
    setActiveGrowthShift(scenario.growthShiftPct);
  };

  const formatCurrency = (valUsd: number) => {
    if (valUsd >= 1000000) return `$${(valUsd / 1000000).toFixed(2)}M`;
    if (valUsd >= 1000) return `$${(valUsd / 1000).toFixed(0)}k`;
    return `$${valUsd.toFixed(0)}`;
  };

  const getCellColor = (months: number) => {
    if (months >= 18) return 'bg-emerald-950/60 border-emerald-500/30 text-emerald-300 hover:bg-emerald-900/80';
    if (months >= 12) return 'bg-amber-950/60 border-amber-500/30 text-amber-300 hover:bg-amber-900/80';
    return 'bg-rose-950/70 border-rose-500/40 text-rose-300 hover:bg-rose-900/80';
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">⚡</span>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Financial Sensitivity &amp; Stress Dashboard
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">
              Downside Protection Engine
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Simulate macroeconomic shocks, burn rate acceleration, and sales cycle headwinds to stress test runway endurance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold block">
              Current Cash Balance
            </span>
            <span className="text-lg font-extrabold text-white font-mono">
              {formatCurrency(baseCashUsd)}
            </span>
          </div>
        </div>
      </div>

      {/* Runway Compression Alert Banner */}
      <div
        className={`p-5 rounded-2xl border transition-all ${
          stressedRunway.alertLevel === 'CRITICAL'
            ? 'bg-rose-950/60 border-rose-500/50 text-rose-200'
            : stressedRunway.alertLevel === 'MODERATE'
            ? 'bg-amber-950/60 border-amber-500/50 text-amber-200'
            : 'bg-emerald-950/60 border-emerald-500/50 text-emerald-200'
        }`}
      >
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-lg">
                {stressedRunway.alertLevel === 'CRITICAL'
                  ? '🚨'
                  : stressedRunway.alertLevel === 'MODERATE'
                  ? '⚠️'
                  : '✅'}
              </span>
              <h3 className="text-base font-bold">
                {stressedRunway.alertLevel === 'CRITICAL'
                  ? 'CRITICAL RUNWAY COMPRESSION ALERT'
                  : stressedRunway.alertLevel === 'MODERATE'
                  ? 'MODERATE RUNWAY WARN'
                  : 'RUNWAY ENDURANCE HEALTHY'}
              </h3>
            </div>
            <p className="text-xs opacity-90">
              Under active scenario (Burn {formatShift(activeBurnShift)}, Growth {formatShift(activeGrowthShift)}), runway shifts from{' '}
              <strong className="underline">{baseRunwayMonths.toFixed(1)} months</strong> to{' '}
              <strong className="underline">{stressedRunway.months.toFixed(1)} months</strong>.
            </p>
          </div>

          <div className="flex items-center gap-4 border-t md:border-t-0 md:border-l border-slate-700/50 pt-3 md:pt-0 md:pl-6">
            <div>
              <span className="text-[10px] uppercase opacity-75 font-mono block">Stressed Burn / Mo</span>
              <span className="text-lg font-extrabold font-mono">
                {formatCurrency(stressedRunway.effectiveBurn)}
              </span>
            </div>
            <div>
              <span className="text-[10px] uppercase opacity-75 font-mono block">Runway Compression</span>
              <span className="text-lg font-extrabold font-mono">
                {stressedRunway.compressionPct > 0
                  ? `-${stressedRunway.compressionPct.toFixed(1)}%`
                  : `+${Math.abs(stressedRunway.compressionPct).toFixed(1)}%`}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Preset Stress Scenarios */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <span>🎮</span> Stress Scenario Presets
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {PRESET_SCENARIOS.map((scenario) => {
            const isSelected = selectedScenarioId === scenario.id;
            return (
              <button
                key={scenario.id}
                onClick={() => handleSelectScenario(scenario)}
                className={`p-4 rounded-xl text-left border transition-all flex flex-col justify-between space-y-3 ${
                  isSelected
                    ? 'bg-indigo-600/30 border-indigo-500 text-white shadow-lg ring-1 ring-indigo-500'
                    : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="flex justify-between items-start">
                  <span className="text-xl">{scenario.icon}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[9px] font-extrabold ${
                      scenario.severityTag === 'CRITICAL'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : scenario.severityTag === 'HIGH'
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}
                  >
                    {scenario.severityTag}
                  </span>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-white mb-1">{scenario.name}</h4>
                  <p className="text-[10px] text-slate-400 leading-relaxed">
                    {scenario.description}
                  </p>
                </div>

                <div className="text-[10px] font-mono text-indigo-300 border-t border-slate-800/80 pt-2 flex justify-between">
                  <span>Burn: {formatShift(scenario.burnShiftPct)}</span>
                  <span>Growth: {formatShift(scenario.growthShiftPct)}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Interactive Sliders & Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex justify-between items-center">
            <label className="text-xs font-bold text-white flex items-center gap-2">
              <span>🔥</span> Monthly Burn Rate Adjustment
            </label>
            <span className="text-xs font-mono font-extrabold text-rose-400">
              {formatShift(activeBurnShift)} ({formatCurrency(stressedRunway.effectiveBurn)}/mo)
            </span>
          </div>

          <input
            type="range"
            min={-40}
            max={60}
            step={5}
            value={activeBurnShift}
            onChange={(e) => {
              setActiveBurnShift(Number(e.target.value));
              setSelectedScenarioId('custom');
            }}
            className="w-full h-2.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-rose-500"
          />

          <div className="flex justify-between text-[10px] font-mono text-slate-400">
            <span>-40% (Aggressive RIF)</span>
            <span>0% (Base Plan)</span>
            <span>+60% (Uncontrolled Burn)</span>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex justify-between items-center">
            <label className="text-xs font-bold text-white flex items-center gap-2">
              <span>📊</span> ARR Revenue Growth Adjustment
            </label>
            <span className="text-xs font-mono font-extrabold text-emerald-400">
              {formatShift(activeGrowthShift)} ({stressedRunway.effectiveArrGrowth.toFixed(1)}% YoY Growth)
            </span>
          </div>

          <input
            type="range"
            min={-50}
            max={50}
            step={5}
            value={activeGrowthShift}
            onChange={(e) => {
              setActiveGrowthShift(Number(e.target.value));
              setSelectedScenarioId('custom');
            }}
            className="w-full h-2.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />

          <div className="flex justify-between text-[10px] font-mono text-slate-400">
            <span>-50% (Sales Stagnation)</span>
            <span>0% (Base Growth)</span>
            <span>+50% (Breakout Growth)</span>
          </div>
        </div>
      </div>

      {/* 5x5 Sensitivity Matrix Grid */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>🧮</span> 5x5 Sensitivity Heatmap Matrix (Runway Months)
            </h3>
            <p className="text-xs text-slate-400">
              Burn Rate Shift (Rows) vs ARR Growth Shift (Columns). Click any cell to inspect scenario.
            </p>
          </div>

          <div className="flex items-center gap-4 text-[11px]">
            <span className="flex items-center gap-1 text-emerald-400">
              <span className="w-2.5 h-2.5 rounded bg-emerald-500 inline-block"></span> &gt;18 Mos
            </span>
            <span className="flex items-center gap-1 text-amber-400">
              <span className="w-2.5 h-2.5 rounded bg-amber-500 inline-block"></span> 12-18 Mos
            </span>
            <span className="flex items-center gap-1 text-rose-400">
              <span className="w-2.5 h-2.5 rounded bg-rose-500 inline-block"></span> &lt;12 Mos (Alert)
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-center text-xs">
            <thead>
              <tr>
                <th className="p-3 text-left font-mono text-[10px] text-slate-400 uppercase tracking-wider">
                  Burn \ Growth
                </th>
                {GROWTH_STEPS.map((g) => (
                  <th key={g} className="p-3 font-mono text-slate-300">
                    {formatShift(g)} Growth
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {matrixData.map((row, rIdx) => {
                const burnDelta = BURN_STEPS[rIdx];
                return (
                  <tr key={burnDelta}>
                    <td className="p-3 text-left font-mono font-bold text-slate-300 bg-slate-900/60">
                      Burn {formatShift(burnDelta)}
                    </td>
                    {row.map((cell) => {
                      const isActiveCell =
                        cell.burn_delta_pct === activeBurnShift &&
                        cell.growth_delta_pct === activeGrowthShift;

                      return (
                        <td
                          key={cell.growth_delta_pct}
                          onClick={() => {
                            setActiveBurnShift(cell.burn_delta_pct);
                            setActiveGrowthShift(cell.growth_delta_pct);
                            setSelectedScenarioId('custom');
                          }}
                          className={`p-4 cursor-pointer border transition-all ${getCellColor(
                            cell.runway_months
                          )} ${
                            isActiveCell ? 'ring-2 ring-indigo-400 scale-105 font-black shadow-lg z-10' : ''
                          }`}
                        >
                          <div className="font-extrabold text-sm font-mono">{cell.runway_months}m</div>
                          <div className="text-[9px] opacity-75 font-mono">
                            {formatCurrency(cell.effective_burn_usd)}/mo
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
