from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Order:
    symbol: str
    target_notional: float
    reason: str


class Broker(Protocol):
    def get_positions(self) -> dict[str, float]:
        ...

    def rebalance(self, orders: list[Order]) -> None:
        ...


@dataclass
class PaperBroker:
    positions: dict[str, float] = field(default_factory=dict)

    def get_positions(self) -> dict[str, float]:
        return dict(self.positions)

    def rebalance(self, orders: list[Order]) -> None:
        for order in orders:
            self.positions[order.symbol] = order.target_notional
            print(
                f"PAPER ORDER {order.symbol}: target_notional={order.target_notional:.2f} reason={order.reason}"
            )
