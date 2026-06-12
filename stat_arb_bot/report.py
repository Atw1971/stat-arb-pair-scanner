from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from stat_arb_bot.backtest import run_backtest
from stat_arb_bot.metrics import pair_stats
from stat_arb_bot.strategy import Side, latest_signal, target_legs


@dataclass(frozen=True)
class TradePlan:
    symbol_a: str
    symbol_b: str
    signal: str
    symbol_a_side: str
    symbol_b_side: str
    entry_reason: str
    action: str
    z_score: float
    hedge_ratio: float
    correlation: float
    half_life: float
    stability: float
    suggested_legs: dict[str, float]
    entry_rule: str
    exit_rule: str
    stop_rule: str
    backtest_trades: int
    backtest_win_rate: float
    backtest_total_spread_pnl: float
    backtest_max_drawdown: float
    notes: str


def build_trade_plan(
    prices: pd.DataFrame,
    symbol_a: str,
    symbol_b: str,
    lookback: int = 120,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    stop_z: float = 3.5,
    notional: float = 10_000,
    cost_bps: float = 4.0,
) -> TradePlan:
    pair = prices[[symbol_a, symbol_b]].dropna()
    signal = latest_signal(
        pair,
        lookback=lookback,
        entry_z=entry_z,
        exit_z=exit_z,
        stop_z=stop_z,
        current_side=Side.FLAT,
    )
    stats = pair_stats(prices[[symbol_a, symbol_b]], symbol_a, symbol_b, lookback, cost_bps=cost_bps)
    backtest = run_backtest(
        pair,
        lookback=lookback,
        entry_z=entry_z,
        exit_z=exit_z,
        stop_z=stop_z,
        cost_bps=cost_bps,
    )
    legs = target_legs(signal, symbol_a, symbol_b, notional)

    if signal.side == Side.LONG_SPREAD:
        signal_name = "LONG_SPREAD"
        symbol_a_side = "LONG"
        symbol_b_side = "SHORT"
        entry_reason = f"z-score <= -{entry_z:.2f}; spread ถูกเมื่อเทียบกับค่าเฉลี่ย"
        action = f"OPEN_POSITION_LONG_SPREAD: long {symbol_a}, short {symbol_b}"
    elif signal.side == Side.SHORT_SPREAD:
        signal_name = "SHORT_SPREAD"
        symbol_a_side = "SHORT"
        symbol_b_side = "LONG"
        entry_reason = f"z-score >= +{entry_z:.2f}; spread แพงเมื่อเทียบกับค่าเฉลี่ย"
        action = f"OPEN_POSITION_SHORT_SPREAD: short {symbol_a}, long {symbol_b}"
    else:
        signal_name = "NO_POSITION"
        symbol_a_side = "NO_POSITION"
        symbol_b_side = "NO_POSITION"
        entry_reason = f"ยังไม่เข้าเงื่อนไข entry; รอ z-score >= +{entry_z:.2f} หรือ <= -{entry_z:.2f}"
        action = "NO_POSITION: no entry signal now"

    return TradePlan(
        symbol_a=symbol_a,
        symbol_b=symbol_b,
        signal=signal_name,
        symbol_a_side=symbol_a_side,
        symbol_b_side=symbol_b_side,
        entry_reason=entry_reason,
        action=action,
        z_score=signal.z,
        hedge_ratio=signal.hedge_ratio,
        correlation=stats.correlation,
        half_life=stats.half_life,
        stability=stats.stability,
        suggested_legs=legs,
        entry_rule=f"Enter when z-score >= {entry_z:.2f} or <= -{entry_z:.2f}",
        exit_rule=f"Close both legs when abs(z-score) <= {exit_z:.2f}",
        stop_rule=f"Close both legs if abs(z-score) >= {stop_z:.2f}",
        backtest_trades=backtest.trade_count,
        backtest_win_rate=backtest.win_rate,
        backtest_total_spread_pnl=backtest.total_return,
        backtest_max_drawdown=backtest.max_drawdown,
        notes="Use this as a signal plan for another execution robot. Recheck broker costs, lot sizing, slippage, and margin before live trading.",
    )


def plans_to_frame(plans: list[TradePlan]) -> pd.DataFrame:
    rows = []
    for plan in plans:
        row = asdict(plan)
        leg_a = plan.suggested_legs.get(plan.symbol_a, 0.0)
        leg_b = plan.suggested_legs.get(plan.symbol_b, 0.0)
        row["leg_a_notional"] = leg_a
        row["leg_b_notional"] = leg_b
        if leg_a and leg_b:
            smaller_leg = min(abs(leg_a), abs(leg_b))
            larger_leg = max(abs(leg_a), abs(leg_b))
            notional_ratio = larger_leg / smaller_leg
        else:
            notional_ratio = 0.0

        row["leg_notional_ratio"] = notional_ratio
        if notional_ratio >= 5:
            row["risk_warning"] = (
                "HIGH_RISK: ขนาดสองฝั่งต่างกันมากเกินไป "
                f"({notional_ratio:.1f}x) ควรลดขนาด position หรือตัดคู่นี้ออก"
            )
        elif notional_ratio >= 3:
            row["risk_warning"] = (
                "CAUTION: ขนาดสองฝั่งต่างกันค่อนข้างมาก "
                f"({notional_ratio:.1f}x) ตรวจ margin, slippage และ lot size ก่อนเปิดจริง"
            )
        elif notional_ratio > 0:
            row["risk_warning"] = "OK: ขนาดสองฝั่งไม่ต่างกันมาก"
        else:
            row["risk_warning"] = "NO_POSITION: ยังไม่มี position ให้ประเมินขนาด"
        row.pop("suggested_legs")
        rows.append(row)
    return pd.DataFrame(rows)
