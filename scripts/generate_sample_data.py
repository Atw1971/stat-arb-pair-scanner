#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    np.random.seed(42)
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    index = pd.date_range("2026-01-01", periods=800, freq="h", tz="UTC")
    returns = np.random.normal(0, 0.0018, len(index))
    base = 100 * np.exp(np.cumsum(returns))

    spread = np.zeros(len(index))
    for i in range(1, len(index)):
        spread[i] = 0.92 * spread[i - 1] + np.random.normal(0, 0.12)

    alpha = base + spread
    beta = base * 0.98 + np.random.normal(0, 0.04, len(index))
    gamma = 75 * np.exp(np.cumsum(np.random.normal(0, 0.004, len(index))))

    for symbol, close in {"ALPHA": alpha, "BETA": beta, "GAMMA": gamma}.items():
        bid = close * 0.9999
        ask = close * 1.0001
        pd.DataFrame(
            {
                "timestamp": index,
                "bid": bid,
                "ask": ask,
                "close": close,
            }
        ).to_csv(output_dir / f"{symbol}.csv", index=False)

    print("Generated sample files: data/ALPHA.csv, data/BETA.csv, data/GAMMA.csv")


if __name__ == "__main__":
    main()
