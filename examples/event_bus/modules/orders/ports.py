from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Order:
    id: str
    user_id: str
    product: str
    quantity: int
    total: Decimal


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> None: ...
