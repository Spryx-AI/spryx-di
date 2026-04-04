from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    id: str
    user_id: str
    product: str
    quantity: int


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> None: ...

    @abstractmethod
    def list_by_user(self, user_id: str) -> list[Order]: ...
