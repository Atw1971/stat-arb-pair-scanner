from __future__ import annotations

from itertools import combinations

import pandas as pd

from stat_arb_bot.metrics import PairStats, pair_stats


def scan_pairs(
    prices: pd.DataFrame,
    lookback: int = 120,
    min_correlation: float = 0.75,
    min_stability: float = 0.70,
    min_half_life: float = 2,
    max_half_life: float = 80,
    max_cost_bps: float = 8,
) -> pd.DataFrame:
    diagnostics = scan_pair_diagnostics(
        prices=prices,
        lookback=lookback,
        min_correlation=min_correlation,
        min_stability=min_stability,
        min_half_life=min_half_life,
        max_half_life=max_half_life,
        max_cost_bps=max_cost_bps,
    )

    if diagnostics.empty:
        return diagnostics

    passed = diagnostics[diagnostics["final_status"] == "PASS"].copy()
    return passed.sort_values(["score", "stability", "correlation"], ascending=False)


def scan_pair_diagnostics(
    prices: pd.DataFrame,
    lookback: int = 120,
    min_correlation: float = 0.75,
    min_stability: float = 0.70,
    min_half_life: float = 2,
    max_half_life: float = 80,
    max_cost_bps: float = 8,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    symbols = [column for column in prices.columns if prices[column].dropna().shape[0] >= lookback * 2]

    for symbol_a, symbol_b in combinations(symbols, 2):
        try:
            stats = pair_stats(prices, symbol_a, symbol_b, lookback)
        except Exception:
            continue

        relationship_ok = abs(stats.correlation) >= min_correlation and stats.stability >= min_stability
        half_life_ok = min_half_life <= stats.half_life <= max_half_life
        cost_ok = stats.cost_bps <= max_cost_bps

        if not relationship_ok:
            final_status = "FAIL_RELATIONSHIP"
        elif not half_life_ok:
            final_status = "FAIL_HALF_LIFE"
        elif not cost_ok:
            final_status = "FAIL_COST"
        else:
            final_status = "PASS"

        row = stats.__dict__.copy()
        row.update(
            {
                "relationship_ok": relationship_ok,
                "half_life_ok": half_life_ok,
                "cost_ok": cost_ok,
                "final_status": final_status,
            }
        )
        rows.append(row)

    if not rows:
        return pd.DataFrame(
            columns=[
                "symbol_a",
                "symbol_b",
                "correlation",
                "hedge_ratio",
                "spread_mean",
                "spread_std",
                "half_life",
                "stability",
                "latest_z",
                "cost_bps",
                "score",
                "relationship_ok",
                "half_life_ok",
                "cost_ok",
                "final_status",
            ]
        )

    df = pd.DataFrame(rows)
    return df.sort_values(["final_status", "score", "stability", "correlation"], ascending=[True, False, False, False])
