from __future__ import annotations

from modules.orders.ports import Order, OrderRepository


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._orders: list[Order] = []

    def save(self, order: Order) -> None:
        self._orders.append(order)

    def list_by_user(self, user_id: str) -> list[Order]:
        return [o for o in self._orders if o.user_id == user_id]
