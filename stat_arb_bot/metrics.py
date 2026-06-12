from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PairStats:
    symbol_a: str
    symbol_b: str
    correlation: float
    hedge_ratio: float
    spread_mean: float
    spread_std: float
    half_life: float
    stability: float
    latest_z: float
    cost_bps: float
    score: float


def hedge_ratio(y: pd.Series, x: pd.Series) -> float:
    clean = pd.concat([y, x], axis=1).dropna()
    if len(clean) < 3:
        return float("nan")
    yv = clean.iloc[:, 0].to_numpy(dtype=float)
    xv = clean.iloc[:, 1].to_numpy(dtype=float)
    variance = np.var(xv)
    if variance == 0:
        return float("nan")
    return float(np.cov(yv, xv, ddof=0)[0, 1] / variance)


def make_spread(y: pd.Series, x: pd.Series, beta: float) -> pd.Series:
    return y - beta * x


def zscore(series: pd.Series, lookback: int) -> pd.Series:
    mean = series.rolling(lookback).mean()
    std = series.rolling(lookback).std(ddof=0)
    return (series - mean) / std.replace(0, np.nan)


def estimate_half_life(spread: pd.Series) -> float:
    clean = spread.dropna()
    if len(clean) < 20:
        return float("inf")

    lagged = clean.shift(1).dropna()
    delta = clean.diff().dropna()
    aligned = pd.concat([delta, lagged], axis=1).dropna()
    y = aligned.iloc[:, 0].to_numpy(dtype=float)
    x = aligned.iloc[:, 1].to_numpy(dtype=float)
    x = x - x.mean()

    denom = np.dot(x, x)
    if denom == 0:
        return float("inf")
    beta = float(np.dot(x, y) / denom)
    if beta >= 0:
        return float("inf")
    return float(-np.log(2) / beta)


def rolling_correlation_stability(a: pd.Series, b: pd.Series, lookback: int) -> float:
    returns = pd.concat([a.pct_change(), b.pct_change()], axis=1).dropna()
    if len(returns) < lookback * 2:
        return 0.0
    rolling_corr = returns.iloc[:, 0].rolling(lookback).corr(returns.iloc[:, 1]).dropna()
    if rolling_corr.empty:
        return 0.0
    positive_ratio = float((rolling_corr > 0).mean())
    low_vol_penalty = max(0.0, 1.0 - float(rolling_corr.std(ddof=0)))
    return positive_ratio * low_vol_penalty


def estimate_cost_bps(a: pd.Series, b: pd.Series, default_bps: float = 2.0) -> float:
    # Without bid/ask data, use a conservative placeholder per leg.
    return default_bps * 2


def pair_stats(
    prices: pd.DataFrame,
    symbol_a: str,
    symbol_b: str,
    lookback: int,
    cost_bps: float | None = None,
) -> PairStats:
    a = prices[symbol_a].dropna()
    b = prices[symbol_b].dropna()
    pair = pd.concat([a, b], axis=1).dropna()
    a = pair.iloc[:, 0]
    b = pair.iloc[:, 1]

    corr = float(np.log(a).corr(np.log(b)))
    beta = hedge_ratio(a, b)
    spread = make_spread(a, b, beta)
    spread_mean = float(spread.rolling(lookback).mean().iloc[-1])
    spread_std = float(spread.rolling(lookback).std(ddof=0).iloc[-1])
    latest_z = float(zscore(spread, lookback).iloc[-1])
    half_life = estimate_half_life(spread)
    stability = rolling_correlation_stability(a, b, lookback)
    trade_cost_bps = cost_bps if cost_bps is not None else estimate_cost_bps(a, b)

    if not np.isfinite(spread_std) or spread_std == 0:
        score = -999.0
    else:
        mean_reversion_score = 1.0 / max(half_life, 1.0) if np.isfinite(half_life) else 0.0
        score = (abs(corr) * 2.0) + stability + mean_reversion_score - (trade_cost_bps / 100.0)

    return PairStats(
        symbol_a=symbol_a,
        symbol_b=symbol_b,
        correlation=corr,
        hedge_ratio=beta,
        spread_mean=spread_mean,
        spread_std=spread_std,
        half_life=half_life,
        stability=stability,
        latest_z=latest_z,
        cost_bps=trade_cost_bps,
        score=float(score),
    )
