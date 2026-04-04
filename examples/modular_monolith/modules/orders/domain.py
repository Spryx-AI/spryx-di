from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class OrderItem:
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal


@dataclass(frozen=True)
class Order:
    id: str
    user_id: str
    user_name: str
    items: list[OrderItem] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        return sum((item.unit_price * item.quantity for item in self.items), Decimal(0))
