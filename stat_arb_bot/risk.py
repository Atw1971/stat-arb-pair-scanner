from __future__ import annotations


def cap_notional(requested: float, max_position_value: float) -> float:
    return max(-max_position_value, min(max_position_value, requested))


def position_notional(equity: float, risk_per_trade: float, stop_z: float, spread_std: float) -> float:
    if stop_z <= 0 or spread_std <= 0:
        return 0.0
    risk_amount = equity * risk_per_trade
    return risk_amount / (stop_z * spread_std)
