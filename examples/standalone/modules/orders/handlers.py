"""Order handlers — ZERO imports from spryx_di.

Dependencies are declared via __init__ type hints.
The container auto-wires everything at resolution time.

CreateOrderHandler depends on:
  - OrderRepository       (from orders module — own provider)
  - UserReader            (from identity module — via import)
  - NotificationSender    (from notifications module — via import)
"""

from __future__ import annotations

import uuid

from modules.identity.ports import UserReader
from modules.notifications.ports import NotificationSender
from modules.orders.ports import Order, OrderRepository


class CreateOrderHandler:
    def __init__(
        self,
        order_repo: OrderRepository,
        user_reader: UserReader,
        notifier: NotificationSender,
    ) -> None:
        self._order_repo = order_repo
        self._user_reader = user_reader
        self._notifier = notifier

    def handle(self, user_id: str, product: str, quantity: int) -> Order:
        user = self._user_reader.get_by_id(user_id)
        if user is None:
            msg = f"User '{user_id}' not found"
            raise ValueError(msg)

        order = Order(
            id=str(uuid.uuid4())[:8],
            user_id=user.id,
            product=product,
            quantity=quantity,
        )
        self._order_repo.save(order)
        self._notifier.send(user.id, f"Pedido #{order.id} criado: {quantity}x {product}")
        return order


class ListUserOrdersHandler:
    def __init__(self, order_repo: OrderRepository) -> None:
        self._order_repo = order_repo

    def handle(self, user_id: str) -> list[Order]:
        return self._order_repo.list_by_user(user_id)
