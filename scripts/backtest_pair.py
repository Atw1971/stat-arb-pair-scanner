#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stat_arb_bot.backtest import run_backtest
from stat_arb_bot.data import load_pair


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest one statistical arbitrage pair.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--symbol-a", required=True)
    parser.add_argument("--symbol-b", required=True)
    parser.add_argument("--lookback", type=int, default=120)
    parser.add_argument("--entry-z", type=float, default=2.0)
    parser.add_argument("--exit-z", type=float, default=0.5)
    parser.add_argument("--stop-z", type=float, default=3.5)
    parser.add_argument("--cost-bps", type=float, default=4.0)
    parser.add_argument("--trades-output", default="trades.csv")
    args = parser.parse_args()

    pair = load_pair(args.data_dir, args.symbol_a, args.symbol_b)
    result = run_backtest(
        pair,
        lookback=args.lookback,
        entry_z=args.entry_z,
        exit_z=args.exit_z,
        stop_z=args.stop_z,
        cost_bps=args.cost_bps,
    )
    result.trades.to_csv(args.trades_output, index=False)

    print(f"Pair: {args.symbol_a.upper()} / {args.symbol_b.upper()}")
    print(f"Trades: {result.trade_count}")
    print(f"Win rate: {result.win_rate:.2%}")
    print(f"Total spread PnL: {result.total_return:.6f}")
    print(f"Max drawdown: {result.max_drawdown:.6f}")
    print(f"Saved trades to {args.trades_output}")


if __name__ == "__main__":
    main()
