from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

from stat_arb_bot.metrics import hedge_ratio, make_spread, zscore


class Side(str, Enum):
    FLAT = "flat"
    LONG_SPREAD = "long_spread"
    SHORT_SPREAD = "short_spread"


@dataclass(frozen=True)
class Signal:
    side: Side
    z: float
    hedge_ratio: float
    reason: str


def latest_signal(
    pair_prices: pd.DataFrame,
    lookback: int = 120,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    stop_z: float = 3.5,
    current_side: Side = Side.FLAT,
) -> Signal:
    a = pair_prices.iloc[:, 0]
    b = pair_prices.iloc[:, 1]
    beta = hedge_ratio(a, b)
    spread = make_spread(a, b, beta)
    latest_z = float(zscore(spread, lookback).iloc[-1])

    if current_side == Side.FLAT:
        if latest_z <= -entry_z:
            return Signal(Side.LONG_SPREAD, latest_z, beta, "spread cheap")
        if latest_z >= entry_z:
            return Signal(Side.SHORT_SPREAD, latest_z, beta, "spread expensive")
        return Signal(Side.FLAT, latest_z, beta, "no entry")

    if abs(latest_z) <= exit_z:
        return Signal(Side.FLAT, latest_z, beta, "take profit: spread normalized")

    if current_side == Side.LONG_SPREAD and latest_z <= -stop_z:
        return Signal(Side.FLAT, latest_z, beta, "stop: spread widened")
    if current_side == Side.SHORT_SPREAD and latest_z >= stop_z:
        return Signal(Side.FLAT, latest_z, beta, "stop: spread widened")

    return Signal(current_side, latest_z, beta, "hold")


def target_legs(signal: Signal, symbol_a: str, symbol_b: str, notional: float) -> dict[str, float]:
    if signal.side == Side.FLAT:
        return {symbol_a: 0.0, symbol_b: 0.0}

    beta_notional = notional * abs(signal.hedge_ratio)
    if signal.side == Side.LONG_SPREAD:
        return {symbol_a: notional, symbol_b: -beta_notional}
    return {symbol_a: -notional, symbol_b: beta_notional}
