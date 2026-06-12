#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stat_arb_bot.data import load_price_matrix
from stat_arb_bot.scanner import scan_pairs


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan assets for statistical arbitrage pairs.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--output", default="pairs.csv")
    parser.add_argument("--lookback", type=int, default=120)
    parser.add_argument("--min-correlation", type=float, default=0.75)
    parser.add_argument("--min-stability", type=float, default=0.70)
    parser.add_argument("--min-half-life", type=float, default=2)
    parser.add_argument("--max-half-life", type=float, default=80)
    parser.add_argument("--max-cost-bps", type=float, default=8)
    args = parser.parse_args()

    prices = load_price_matrix(args.data_dir)
    pairs = scan_pairs(
        prices=prices,
        lookback=args.lookback,
        min_correlation=args.min_correlation,
        min_stability=args.min_stability,
        min_half_life=args.min_half_life,
        max_half_life=args.max_half_life,
        max_cost_bps=args.max_cost_bps,
    )
    pairs.to_csv(args.output, index=False)
    print(pairs.head(20).to_string(index=False))
    print(f"\nSaved {len(pairs)} pairs to {args.output}")


if __name__ == "__main__":
    main()
