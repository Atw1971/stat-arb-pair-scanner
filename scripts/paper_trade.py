#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stat_arb_bot.broker import Order, PaperBroker
from stat_arb_bot.data import load_pair
from stat_arb_bot.strategy import Side, latest_signal, target_legs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run paper stat-arb trading loop from CSV prices.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--symbol-a", required=True)
    parser.add_argument("--symbol-b", required=True)
    parser.add_argument("--lookback", type=int, default=120)
    parser.add_argument("--entry-z", type=float, default=2.0)
    parser.add_argument("--exit-z", type=float, default=0.5)
    parser.add_argument("--stop-z", type=float, default=3.5)
    parser.add_argument("--notional", type=float, default=10000)
    parser.add_argument("--interval-seconds", type=float, default=30)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    broker = PaperBroker()
    current_side = Side.FLAT

    while True:
        pair = load_pair(args.data_dir, args.symbol_a, args.symbol_b)
        signal = latest_signal(
            pair,
            lookback=args.lookback,
            entry_z=args.entry_z,
            exit_z=args.exit_z,
            stop_z=args.stop_z,
            current_side=current_side,
        )
        targets = target_legs(signal, args.symbol_a.upper(), args.symbol_b.upper(), args.notional)
        orders = [Order(symbol=symbol, target_notional=value, reason=signal.reason) for symbol, value in targets.items()]
        broker.rebalance(orders)
        current_side = signal.side
        print(f"signal={signal.side.value} z={signal.z:.2f} beta={signal.hedge_ratio:.4f} reason={signal.reason}")

        if args.once:
            break
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
