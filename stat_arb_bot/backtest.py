from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from stat_arb_bot.metrics import hedge_ratio, make_spread, zscore
from stat_arb_bot.strategy import Side


@dataclass(frozen=True)
class BacktestResult:
    trades: pd.DataFrame
    equity: pd.Series
    total_return: float
    max_drawdown: float
    win_rate: float
    trade_count: int


def run_backtest(
    pair_prices: pd.DataFrame,
    lookback: int = 120,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    stop_z: float = 3.5,
    cost_bps: float = 4.0,
) -> BacktestResult:
    pair_prices = pair_prices.dropna()
    a = pair_prices.iloc[:, 0]
    b = pair_prices.iloc[:, 1]
    beta = hedge_ratio(a, b)
    spread = make_spread(a, b, beta)
    z = zscore(spread, lookback)

    side = Side.FLAT
    entry_spread = 0.0
    entry_time = None
    realized = 0.0
    equity_values = []
    trades = []
    cost = cost_bps / 10000.0

    for timestamp, spread_value in spread.items():
        current_z = z.loc[timestamp]
        if pd.isna(current_z):
            equity_values.append((timestamp, realized))
            continue

        if side == Side.FLAT:
            if current_z <= -entry_z:
                side = Side.LONG_SPREAD
                entry_spread = float(spread_value)
                entry_time = timestamp
                realized -= cost
            elif current_z >= entry_z:
                side = Side.SHORT_SPREAD
                entry_spread = float(spread_value)
                entry_time = timestamp
                realized -= cost

        elif side == Side.LONG_SPREAD:
            open_pnl = float(spread_value - entry_spread)
            should_exit = current_z >= -exit_z or current_z <= -stop_z
            if should_exit:
                pnl = open_pnl - cost
                realized += pnl
                trades.append(
                    {
                        "entry_time": entry_time,
                        "exit_time": timestamp,
                        "side": side.value,
                        "entry_spread": entry_spread,
                        "exit_spread": float(spread_value),
                        "pnl": pnl,
                    }
                )
                side = Side.FLAT
                entry_time = None

        elif side == Side.SHORT_SPREAD:
            open_pnl = float(entry_spread - spread_value)
            should_exit = current_z <= exit_z or current_z >= stop_z
            if should_exit:
                pnl = open_pnl - cost
                realized += pnl
                trades.append(
                    {
                        "entry_time": entry_time,
                        "exit_time": timestamp,
                        "side": side.value,
                        "entry_spread": entry_spread,
                        "exit_spread": float(spread_value),
                        "pnl": pnl,
                    }
                )
                side = Side.FLAT
                entry_time = None

        mark_to_market = realized
        if side == Side.LONG_SPREAD:
            mark_to_market += float(spread_value - entry_spread)
        elif side == Side.SHORT_SPREAD:
            mark_to_market += float(entry_spread - spread_value)
        equity_values.append((timestamp, mark_to_market))

    equity = pd.Series(dict(equity_values)).sort_index()
    trades_df = pd.DataFrame(trades)
    total_return = float(equity.iloc[-1]) if not equity.empty else 0.0
    running_max = equity.cummax()
    drawdown = equity - running_max
    max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0
    win_rate = float((trades_df["pnl"] > 0).mean()) if not trades_df.empty else 0.0

    return BacktestResult(
        trades=trades_df,
        equity=equity,
        total_return=total_return,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        trade_count=len(trades_df),
    )
