from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OrderCreated:
    order_id: str
    user_id: str
    product: str
    quantity: int
    total: Decimal
