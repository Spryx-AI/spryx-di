from __future__ import annotations

from modules.orders.domain import Order
from modules.orders.ports import OrderRepository


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._orders[order.id] = order

    def get_by_id(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def list_by_user(self, user_id: str) -> list[Order]:
        return [o for o in self._orders.values() if o.user_id == user_id]
