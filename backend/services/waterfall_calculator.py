from typing import List, Dict, Optional
from backend.domain.schemas import CapTableEntry, WaterfallPayout, WaterfallScenario

def calculate_exit_waterfall(
    cap_table: List[CapTableEntry],
    exit_valuation_usd: float,
    total_investment_usd: float = 0.0
) -> WaterfallScenario:
    """
    Calculates liquidation preference payout first (accounting for 1x/2x multipliers
    and non-participating vs participating shares with caps).
    Distributes remaining proceeds to Common and participating Preferred shares pro-rata based on ownership %.
    Computes MOIC and IRR for each investor share class.
    """
    if not cap_table:
        return WaterfallScenario(exit_valuation_usd=exit_valuation_usd, payouts=[])

    # 1. Determine invested capital per entry
    preferred_entries = [
        entry for entry in cap_table
        if entry.liquidation_preference_multiplier > 0 
        and "common" not in entry.share_class.lower() 
        and "option" not in entry.share_class.lower()
    ]

    total_pref_ownership = sum(e.ownership_pct for e in preferred_entries)

    invested_capital_map: Dict[int, float] = {}
    for idx, entry in enumerate(cap_table):
        is_pref = entry in preferred_entries
        if is_pref and total_investment_usd > 0 and total_pref_ownership > 0:
            invested_capital_map[idx] = total_investment_usd * (entry.ownership_pct / total_pref_ownership)
        elif is_pref and total_investment_usd == 0 and total_pref_ownership > 0:
            # Default fallback for total preferred capital if not provided
            invested_capital_map[idx] = 10_000_000.0 * (entry.ownership_pct / total_pref_ownership)
        else:
            invested_capital_map[idx] = 0.0

    # 2. Determine preference targets and conversion decisions
    converted_to_common = [False] * len(cap_table)
    pref_targets = [0.0] * len(cap_table)

    total_ownership_pct = sum(e.ownership_pct for e in cap_table) or 100.0

    for idx, entry in enumerate(cap_table):
        invested = invested_capital_map[idx]
        is_pref = entry in preferred_entries
        if is_pref:
            target = invested * entry.liquidation_preference_multiplier
            common_payout = exit_valuation_usd * (entry.ownership_pct / total_ownership_pct)

            if not entry.is_participating:
                max_pref_payout = min(exit_valuation_usd, target)
            else:
                if entry.cap_multiplier and entry.cap_multiplier > 0:
                    max_pref_payout = entry.cap_multiplier * invested
                else:
                    max_pref_payout = float('inf')

            if common_payout > max_pref_payout and common_payout > target:
                converted_to_common[idx] = True
                pref_targets[idx] = 0.0
            else:
                pref_targets[idx] = target
        else:
            pref_targets[idx] = 0.0

    # 3. Phase 1: Pay Liquidation Preference
    total_pref_target = sum(pref_targets)
    payouts = [0.0] * len(cap_table)

    if total_pref_target > 0:
        if exit_valuation_usd <= total_pref_target:
            for idx in range(len(cap_table)):
                if pref_targets[idx] > 0:
                    payouts[idx] = exit_valuation_usd * (pref_targets[idx] / total_pref_target)
            remaining_proceeds = 0.0
        else:
            for idx in range(len(cap_table)):
                payouts[idx] = pref_targets[idx]
            remaining_proceeds = exit_valuation_usd - total_pref_target
    else:
        remaining_proceeds = exit_valuation_usd

    # 4. Phase 2: Participate in Remaining Proceeds
    if remaining_proceeds > 0:
        eligible_indices = set()
        for idx, entry in enumerate(cap_table):
            is_common = (
                "common" in entry.share_class.lower() 
                or "option" in entry.share_class.lower() 
                or entry.liquidation_preference_multiplier == 0
            )
            if is_common or converted_to_common[idx] or entry.is_participating:
                eligible_indices.add(idx)

        active_indices = list(eligible_indices)

        while remaining_proceeds > 1e-6 and active_indices:
            active_ownership = sum(cap_table[i].ownership_pct for i in active_indices)
            if active_ownership <= 0:
                break

            capped_in_this_round = []
            for i in active_indices:
                entry = cap_table[i]
                prop_add = remaining_proceeds * (entry.ownership_pct / active_ownership)

                if entry.is_participating and not converted_to_common[i] and entry.cap_multiplier and entry.cap_multiplier > 0:
                    invested = invested_capital_map[i]
                    max_total = entry.cap_multiplier * invested
                    max_add = max(0.0, max_total - payouts[i])
                    if prop_add >= max_add - 1e-6:
                        capped_in_this_round.append((i, max_add))

            if capped_in_this_round:
                for idx_capped, max_add in capped_in_this_round:
                    payouts[idx_capped] += max_add
                    remaining_proceeds -= max_add
                    if idx_capped in active_indices:
                        active_indices.remove(idx_capped)
                remaining_proceeds = max(0.0, remaining_proceeds)
            else:
                for i in active_indices:
                    payouts[i] += remaining_proceeds * (cap_table[i].ownership_pct / active_ownership)
                remaining_proceeds = 0.0

    # 5. Compute MOIC and IRR for each investor share class
    results: List[WaterfallPayout] = []
    for idx, entry in enumerate(cap_table):
        payout_usd = round(payouts[idx], 2)
        invested = invested_capital_map[idx]

        if invested > 0:
            moic = round(payout_usd / invested, 2)
            if payout_usd > 0:
                irr_pct = round(((payout_usd / invested) ** (1.0 / 5.0) - 1.0) * 100.0, 2)
            else:
                irr_pct = -100.0
        else:
            moic = 0.0
            irr_pct = 0.0

        results.append(
            WaterfallPayout(
                share_class=entry.share_class,
                investor_name=entry.investor_name,
                payout_usd=payout_usd,
                moic=moic,
                irr_pct=irr_pct
            )
        )

    return WaterfallScenario(
        exit_valuation_usd=exit_valuation_usd,
        payouts=results
    )

def generate_waterfall_curve(
    cap_table: List[CapTableEntry],
    exit_valuations: List[float],
    total_investment_usd: float = 0.0
) -> List[WaterfallScenario]:
    """
    Generates waterfall scenarios across a range of exit valuations.
    """
    scenarios = []
    for exit_val in exit_valuations:
        scenarios.append(calculate_exit_waterfall(cap_table, exit_val, total_investment_usd))
    return scenarios
