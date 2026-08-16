import React, { useState, useMemo } from 'react';
import { CapTableEntry, WaterfallScenarioPayout } from '../types';

const DEFAULT_CAP_TABLE: CapTableEntry[] = [
  {
    id: 'ct-1',
    shareholder_name: 'Series B Ventures (Lead)',
    share_class: 'Series B Preferred',
    shares: 2500000,
    ownership_pct: 20.0,
    investment_usd: 15000000,
    liquidation_preference_multiplier: 1.0,
    seniority: 1,
    participating: false,
  },
  {
    id: 'ct-2',
    shareholder_name: 'Series A Capital & Co',
    share_class: 'Series A Preferred',
    shares: 3125000,
    ownership_pct: 25.0,
    investment_usd: 10000000,
    liquidation_preference_multiplier: 1.0,
    seniority: 2,
    participating: false,
  },
  {
    id: 'ct-3',
    shareholder_name: 'Seed Angels Syndicate',
    share_class: 'Seed Preferred',
    shares: 1875000,
    ownership_pct: 15.0,
    investment_usd: 3000000,
    liquidation_preference_multiplier: 1.0,
    seniority: 3,
    participating: false,
  },
  {
    id: 'ct-4',
    shareholder_name: 'Founders & Core Team',
    share_class: 'Founders Common',
    shares: 3750000,
    ownership_pct: 30.0,
    investment_usd: 100000,
    liquidation_preference_multiplier: 0.0,
    seniority: 4,
    participating: false,
  },
  {
    id: 'ct-5',
    shareholder_name: 'Unallocated Option Pool',
    share_class: 'Employee Options',
    shares: 1250000,
    ownership_pct: 10.0,
    investment_usd: 0,
    liquidation_preference_multiplier: 0.0,
    seniority: 4,
    participating: false,
  },
];

export const CapTableWaterfallView: React.FC = () => {
  const [capTable, setCapTable] = useState<CapTableEntry[]>(DEFAULT_CAP_TABLE);
  const [exitValuationM, setExitValuationM] = useState<number>(150); // $150M default
  const [showEditor, setShowEditor] = useState<boolean>(false);

  // Total shares count
  const totalShares = useMemo(() => {
    return capTable.reduce((acc, item) => acc + item.shares, 0);
  }, [capTable]);

  // Waterfall Calculation Engine
  const waterfallResult = useMemo(() => {
    const exitValuationUsd = exitValuationM * 1000000;
    let remainingDistributableUsd = exitValuationUsd;

    // Group preferred classes by seniority ascending (1 = highest)
    const sortedEntries = [...capTable].sort((a, b) => a.seniority - b.seniority);

    // Initial payout object mapping id -> preference & common
    const payoutMap: Record<string, { preference: number; common: number; total: number }> = {};
    sortedEntries.forEach((entry) => {
      payoutMap[entry.id] = { preference: 0, common: 0, total: 0 };
    });

    // Step 1: Pay Liquidation Preferences by Seniority
    // Higher seniority gets 100% of preference before lower seniority
    const seniorityGroups = Array.from(new Set(sortedEntries.map((e) => e.seniority))).sort(
      (a, b) => a - b
    );

    for (const seniority of seniorityGroups) {
      const groupEntries = sortedEntries.filter(
        (e) => e.seniority === seniority && e.liquidation_preference_multiplier > 0
      );

      const totalGroupPref = groupEntries.reduce(
        (acc, entry) => acc + entry.investment_usd * entry.liquidation_preference_multiplier,
        0
      );

      if (totalGroupPref > 0) {
        if (remainingDistributableUsd >= totalGroupPref) {
          // Full preference paid
          groupEntries.forEach((entry) => {
            const prefAmount = entry.investment_usd * entry.liquidation_preference_multiplier;
            payoutMap[entry.id].preference = prefAmount;
          });
          remainingDistributableUsd -= totalGroupPref;
        } else {
          // Pro-rata payout of remaining cash for this seniority tier
          groupEntries.forEach((entry) => {
            const prefAmount = entry.investment_usd * entry.liquidation_preference_multiplier;
            const proRataShare = prefAmount / totalGroupPref;
            payoutMap[entry.id].preference = remainingDistributableUsd * proRataShare;
          });
          remainingDistributableUsd = 0;
          break;
        }
      }
    }

    // Step 2: Evaluate conversion to Common vs. taking Liquidation Preference
    // For non-participating preferred, holders will choose Common conversion if pro-rata common value > preference payout
    // Iterate to find optimal choice for each preferred class:
    let convertCommonShares = 0;
    const convertingIds = new Set<string>();

    // Common shares always convert
    sortedEntries.forEach((entry) => {
      if (entry.liquidation_preference_multiplier === 0) {
        convertCommonShares += entry.shares;
        convertingIds.add(entry.id);
      }
    });

    // Determine which preferred classes gain more by converting to common
    // If converted, total common pool includes their shares & dist distibutable proceeds includes their pref cash back
    // Standard waterfall check:
    let loopChanged = true;
    while (loopChanged) {
      loopChanged = false;
      const currentCommonPool = sortedEntries.reduce(
        (sum, entry) => (convertingIds.has(entry.id) ? sum + entry.shares : sum),
        0
      );

      // Total distributable if converting preferreds give up their pref
      const prefGivenUp = sortedEntries.reduce(
        (sum, entry) => (convertingIds.has(entry.id) ? sum + payoutMap[entry.id].preference : 0),
        0
      );
      const totalCommonDistributable = remainingDistributableUsd + prefGivenUp;

      for (const entry of sortedEntries) {
        if (entry.liquidation_preference_multiplier > 0 && !convertingIds.has(entry.id)) {
          const commonShareRatio = entry.shares / (currentCommonPool + entry.shares);
          const potentialCommonPayout = totalCommonDistributable * commonShareRatio;

          if (potentialCommonPayout > payoutMap[entry.id].preference) {
            convertingIds.add(entry.id);
            loopChanged = true;
            break;
          }
        }
      }
    }

    // Recalculate Final Common Distribution with converting share classes
    const finalCommonShares = sortedEntries.reduce(
      (sum, entry) => (convertingIds.has(entry.id) ? sum + entry.shares : sum),
      0
    );

    const finalPrefPaid = sortedEntries.reduce(
      (sum, entry) => (!convertingIds.has(entry.id) ? sum + payoutMap[entry.id].preference : 0),
      0
    );

    const finalCommonPoolUsd = Math.max(0, exitValuationUsd - finalPrefPaid);

    const payouts: WaterfallScenarioPayout[] = sortedEntries.map((entry) => {
      const isConverting = convertingIds.has(entry.id);
      let prefPayout = 0;
      let commonPayout = 0;

      if (isConverting) {
        prefPayout = 0;
        commonPayout = (entry.shares / finalCommonShares) * finalCommonPoolUsd;
      } else {
        prefPayout = payoutMap[entry.id].preference;
        commonPayout = 0;
      }

      const totalPayout = prefPayout + commonPayout;
      const moic = entry.investment_usd > 0 ? totalPayout / entry.investment_usd : totalPayout > 0 ? 999.0 : 0.0;
      const returnPct = entry.investment_usd > 0 ? ((totalPayout - entry.investment_usd) / entry.investment_usd) * 100 : 0;
      const effectiveOwnership = exitValuationUsd > 0 ? (totalPayout / exitValuationUsd) * 100 : 0;

      return {
        share_class: entry.share_class,
        shareholder_name: entry.shareholder_name,
        preference_payout_usd: prefPayout,
        common_payout_usd: commonPayout,
        total_payout_usd: totalPayout,
        moic: Number(moic.toFixed(2)),
        return_pct: Number(returnPct.toFixed(1)),
        effective_ownership_pct: Number(effectiveOwnership.toFixed(1)),
      };
    });

    const commonTotalUsd = payouts
      .filter((p) => p.share_class.includes('Common') || p.share_class.includes('Option'))
      .reduce((acc, p) => acc + p.total_payout_usd, 0);

    const preferredTotalUsd = payouts
      .filter((p) => p.share_class.includes('Preferred'))
      .reduce((acc, p) => acc + p.total_payout_usd, 0);

    return {
      payouts,
      commonTotalUsd,
      preferredTotalUsd,
      exitValuationUsd,
    };
  }, [capTable, exitValuationM]);

  const formatCurrency = (valUsd: number) => {
    if (valUsd >= 1000000000) {
      return `$${(valUsd / 1000000000).toFixed(2)}B`;
    }
    if (valUsd >= 1000000) {
      return `$${(valUsd / 1000000).toFixed(2)}M`;
    }
    if (valUsd >= 1000) {
      return `$${(valUsd / 1000).toFixed(0)}k`;
    }
    return `$${valUsd.toFixed(0)}`;
  };

  const getMoicBadgeClass = (moic: number) => {
    if (moic >= 3.0) return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    if (moic >= 1.0) return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
    return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
  };

  const handleUpdateEntry = (id: string, key: keyof CapTableEntry, value: any) => {
    setCapTable((prev) =>
      prev.map((item) => (item.id === id ? { ...item, [key]: value } : item))
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">📊</span>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Cap Table &amp; Exit Waterfall Simulator
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Institutional Grade
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Simulate liquidity preference stack, conversion hurdles, pro-rata common distributions, and MOIC returns across exit valuations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowEditor(!showEditor)}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 text-slate-200 hover:text-white hover:bg-slate-700 transition-colors border border-slate-700"
          >
            {showEditor ? 'Hide Cap Table Config' : '⚙️ Edit Cap Table'}
          </button>
        </div>
      </div>

      {/* Interactive Exit Valuation Slider & Presets */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <div>
            <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">
              Exit Valuation Simulator
            </span>
            <div className="text-3xl font-extrabold text-indigo-400 tracking-tight">
              {formatCurrency(exitValuationM * 1000000)}
            </div>
          </div>

          {/* Preset Buttons */}
          <div className="flex flex-wrap gap-2">
            {[
              { label: '$25M Distressed', val: 25 },
              { label: '$75M M&A', val: 75 },
              { label: '$150M Base', val: 150 },
              { label: '$350M Growth', val: 350 },
              { label: '$1.0B Unicorn', val: 1000 },
            ].map((preset) => (
              <button
                key={preset.val}
                onClick={() => setExitValuationM(preset.val)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all border ${
                  exitValuationM === preset.val
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-md'
                    : 'bg-slate-900/60 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Range Slider */}
        <div className="space-y-1">
          <input
            type="range"
            min={10}
            max={1000}
            step={5}
            value={exitValuationM}
            onChange={(e) => setExitValuationM(Number(e.target.value))}
            className="w-full h-2.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
          <div className="flex justify-between text-[10px] font-mono text-slate-400">
            <span>$10M (Downside)</span>
            <span>$250M</span>
            <span>$500M</span>
            <span>$750M</span>
            <span>$1,000M ($1B IPO)</span>
          </div>
        </div>
      </div>

      {/* Visual Bar Breakdown & Summary Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Payout Bar Breakdown */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>📈</span> Payout Distribution Stack
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              Total Proceeds: {formatCurrency(waterfallResult.exitValuationUsd)}
            </span>
          </div>

          {/* Stacked Progress Bar */}
          <div className="h-6 w-full bg-slate-900 rounded-xl overflow-hidden flex border border-slate-800">
            {waterfallResult.payouts.map((payout, idx) => {
              const colors = [
                'bg-indigo-500',
                'bg-cyan-500',
                'bg-teal-500',
                'bg-emerald-500',
                'bg-amber-500',
              ];
              const color = colors[idx % colors.length];
              const widthPct = payout.effective_ownership_pct;

              return (
                <div
                  key={payout.share_class}
                  style={{ width: `${widthPct}%` }}
                  className={`${color} h-full transition-all duration-300 relative group`}
                  title={`${payout.shareholder_name}: ${formatCurrency(payout.total_payout_usd)} (${widthPct}%)`}
                />
              );
            })}
          </div>

          {/* Individual Shareholder Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            {waterfallResult.payouts.map((payout, idx) => {
              const borderColors = [
                'border-indigo-500/40',
                'border-cyan-500/40',
                'border-teal-500/40',
                'border-emerald-500/40',
                'border-amber-500/40',
              ];
              const borderColor = borderColors[idx % borderColors.length];

              return (
                <div
                  key={payout.share_class}
                  className={`p-3.5 rounded-xl bg-slate-900/60 border ${borderColor} space-y-1.5`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-xs font-bold text-slate-200 block truncate">
                        {payout.shareholder_name}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {payout.share_class}
                      </span>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getMoicBadgeClass(
                        payout.moic
                      )}`}
                    >
                      {payout.moic > 0 ? `${payout.moic.toFixed(2)}x MOIC` : 'N/A'}
                    </span>
                  </div>

                  <div className="flex justify-between items-baseline pt-1 border-t border-slate-800/80">
                    <span className="text-xs text-slate-400">Total Payout:</span>
                    <span className="text-sm font-extrabold text-white">
                      {formatCurrency(payout.total_payout_usd)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Summary Card */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <span>⚖️</span> Waterfall Summary
            </h3>

            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex justify-between items-center">
                <span className="text-xs text-slate-400">Preferred Capital Returned</span>
                <span className="text-sm font-bold text-emerald-400">
                  {formatCurrency(waterfallResult.preferredTotalUsd)}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex justify-between items-center">
                <span className="text-xs text-slate-400">Common &amp; ESOP Proceeds</span>
                <span className="text-sm font-bold text-indigo-400">
                  {formatCurrency(waterfallResult.commonTotalUsd)}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex justify-between items-center">
                <span className="text-xs text-slate-400">Lead Investor (Series B) Payout</span>
                <span className="text-sm font-bold text-cyan-400">
                  {formatCurrency(waterfallResult.payouts[0]?.total_payout_usd || 0)}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex justify-between items-center">
                <span className="text-xs text-slate-400">Lead Investor MOIC</span>
                <span className="text-sm font-extrabold text-white">
                  {waterfallResult.payouts[0]?.moic || 0}x
                </span>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300">
            💡 <strong>Waterfall Logic:</strong> Liquidation preferences are paid in order of seniority (Series B &gt; Series A &gt; Seed). Conversion to Common occurs when pro-rata common payout exceeds 1.0x preference payout.
          </div>
        </div>
      </div>

      {/* Detailed Cap Table & Payout Table */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <span>📋</span> Share Class &amp; Waterfall Breakdown
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3 px-3">Shareholder</th>
                <th className="py-3 px-3">Share Class</th>
                <th className="py-3 px-3 text-right">Shares</th>
                <th className="py-3 px-3 text-right">Ownership</th>
                <th className="py-3 px-3 text-right">Invested ($)</th>
                <th className="py-3 px-3 text-center">Pref Multiplier</th>
                <th className="py-3 px-3 text-right">Payout ($)</th>
                <th className="py-3 px-3 text-center">MOIC</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {waterfallResult.payouts.map((payout) => {
                const entry = capTable.find((e) => e.share_class === payout.share_class);
                return (
                  <tr key={payout.share_class} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-3 font-semibold text-white">
                      {payout.shareholder_name}
                    </td>
                    <td className="py-3 px-3 text-slate-300 font-mono">{payout.share_class}</td>
                    <td className="py-3 px-3 text-right font-mono text-slate-300">
                      {entry?.shares.toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-300">
                      {entry?.ownership_pct.toFixed(1)}%
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-300">
                      {entry?.investment_usd ? formatCurrency(entry.investment_usd) : '$0'}
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-slate-400">
                      {entry?.liquidation_preference_multiplier
                        ? `${entry.liquidation_preference_multiplier}x`
                        : 'None'}
                    </td>
                    <td className="py-3 px-3 text-right font-bold font-mono text-indigo-300">
                      {formatCurrency(payout.total_payout_usd)}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded text-[11px] font-bold border ${getMoicBadgeClass(
                          payout.moic
                        )}`}
                      >
                        {payout.moic > 0 ? `${payout.moic.toFixed(2)}x` : 'N/A'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Optional Cap Table Editor Modal / Expandable Panel */}
      {showEditor && (
        <div className="glass-panel p-6 rounded-2xl border border-indigo-500/30 bg-slate-900/90 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <span>⚙️</span> Interactive Cap Table Structure Editor
          </h3>

          <div className="space-y-3">
            {capTable.map((entry) => (
              <div
                key={entry.id}
                className="grid grid-cols-1 sm:grid-cols-5 gap-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800 items-center text-xs"
              >
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1">Shareholder</label>
                  <input
                    type="text"
                    value={entry.shareholder_name}
                    onChange={(e) => handleUpdateEntry(entry.id, 'shareholder_name', e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-semibold"
                  />
                </div>

                <div>
                  <label className="text-[10px] text-slate-400 block mb-1">Share Class</label>
                  <input
                    type="text"
                    value={entry.share_class}
                    onChange={(e) => handleUpdateEntry(entry.id, 'share_class', e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-mono"
                  />
                </div>

                <div>
                  <label className="text-[10px] text-slate-400 block mb-1">Shares Count</label>
                  <input
                    type="number"
                    value={entry.shares}
                    onChange={(e) => handleUpdateEntry(entry.id, 'shares', Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-mono"
                  />
                </div>

                <div>
                  <label className="text-[10px] text-slate-400 block mb-1">Invested Capital ($)</label>
                  <input
                    type="number"
                    value={entry.investment_usd}
                    onChange={(e) => handleUpdateEntry(entry.id, 'investment_usd', Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-mono"
                  />
                </div>

                <div>
                  <label className="text-[10px] text-slate-400 block mb-1">Liquidation Pref Multiplier</label>
                  <input
                    type="number"
                    step="0.25"
                    value={entry.liquidation_preference_multiplier}
                    onChange={(e) =>
                      handleUpdateEntry(entry.id, 'liquidation_preference_multiplier', Number(e.target.value))
                    }
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-mono"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
