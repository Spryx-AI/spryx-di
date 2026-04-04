from __future__ import annotations

from abc import ABC, abstractmethod

from modules.orders.domain import Order


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> None: ...

    @abstractmethod
    def get_by_id(self, order_id: str) -> Order | None: ...

    @abstractmethod
    def list_by_user(self, user_id: str) -> list[Order]: ...
